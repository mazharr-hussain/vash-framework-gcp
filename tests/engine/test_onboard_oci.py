import json
import subprocess
from pathlib import Path

import pytest

from vash.adapters.cloud.oci import adapter as tf_module
from vash.adapters.cloud.oci.onboard import Onboarding, Options
from vash.cli.main import main
from vash.core.exceptions import AdapterNotInstalled, VashError

TENANCY = "ocid1.tenancy.oc1..t"
COMPARTMENT = "ocid1.compartment.oc1..c"
ENV = {"OCI_CLI_CLOUD_SHELL": "True", "OCI_TENANCY": TENANCY, "OCI_REGION": "eu-frankfurt-1"}


def done(stdout="", code=0, stderr=""):
    return subprocess.CompletedProcess([], code, stdout=stdout, stderr=stderr)


class FakeCloud:
    """Answers the oci, ssh and ssh-keygen calls the onboarding makes."""

    def __init__(self, quota=None, compartments=(), images=("ocid1.image.oc1..u",), ready="vash=vash 3.0.0"):
        self.quota = quota or {"AD-1": (4, 24)}
        self.compartments = list(compartments)
        self.images = list(images)
        self.ready = ready
        self.calls = []
        self.subnet = {"display-name": "public subnet-PoC", "prohibit-public-ip-on-vnic": False,
                       "security-list-ids": ["ocid1.securitylist..a"]}
        self.ingress = [{"protocol": "6", "source": "0.0.0.0/0",
                         "tcp-options": {"destination-port-range": {"min": 22, "max": 22}}}]

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[0] == "oci":
            return done(json.dumps(self.oci(args[1:])))
        if args[0] == "ssh-keygen":
            key = Path(args[args.index("-f") + 1])
            key.write_text("private")
            key.with_suffix(".pub").write_text("ssh-ed25519 AAAA test")
            return done()
        if args[0] == "ssh":
            if "cat /var/lib/vash/ready" in args[-1]:
                return done(self.ready) if self.ready else done(code=255)
            return done()
        raise AssertionError(f"unexpected command {args}")

    def oci(self, args):
        if args[:3] == ["iam", "compartment", "list"]:
            return {"data": [{"id": c} for c in self.compartments]}
        if args[:3] == ["iam", "compartment", "create"]:
            return {"data": {"id": COMPARTMENT}}
        if args[:3] == ["iam", "availability-domain", "list"]:
            return {"data": [{"name": ad} for ad in self.quota]}
        if args[:3] == ["limits", "resource-availability", "get"]:
            ad = args[args.index("--availability-domain") + 1]
            cores, memory = self.quota[ad]
            limit = args[args.index("--limit-name") + 1]
            return {"data": {"available": cores if "core" in limit else memory}}
        if args[:3] == ["network", "subnet", "get"]:
            return {"data": self.subnet}
        if args[:3] == ["network", "security-list", "get"]:
            return {"data": {"ingress-security-rules": self.ingress}}
        if args[:3] == ["compute", "image", "list"]:
            return {"data": [{"id": i, "display-name": "Ubuntu-24.04-aarch64"} for i in self.images]}
        raise AssertionError(f"unexpected oci call {args}")


class FakeTerraform:
    def __init__(self, capacity_fail=()):
        self.capacity_fail = set(capacity_fail)
        self.calls = []

    def __call__(self, cmd, cwd=None, **kwargs):
        self.calls.append((cmd, Path(cwd)))
        if cmd[1] == "apply":
            ad = json.loads((Path(cwd) / "terraform.tfvars.json").read_text())["availability_domain"]
            if ad in self.capacity_fail:
                return done(code=1, stderr="Error: 500-InternalError, Out of host capacity.")
        if cmd[1] == "output":
            return done(json.dumps({"runner_ip": {"value": "203.0.113.7"}}))
        return done()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


def make(cloud, home, **opts):
    opts.setdefault("name_prefix", "north")
    opts.setdefault("compartment_name", "vash")
    options = Options(admin_cidr="198.51.100.1/32", workdir=home / ".vash" / "oci", **opts)
    return Onboarding(options, run=cloud, echo=lambda _m: None, sleep=lambda _s: None, env=ENV)


def test_up_creates_vm_and_installs(home, monkeypatch):
    cloud, tf = FakeCloud(), FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    assert make(cloud, home).up() == 0
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["compartment_id"] == COMPARTMENT
    assert tfvars["availability_domain"] == "AD-1"
    assert tfvars["oci_auth"] == "InstancePrincipal"
    assert tfvars["admin_cidr"] == "198.51.100.1/32"
    assert tfvars["cloud_init_script"] == "vash-runner.sh"
    script = (home / ".vash/oci/environments/always-free/scripts/vash-runner.sh").read_text()
    assert "@@" not in script and "qwen2.5-coder:7b" in script
    assert [c[0][1] for c in tf.calls] == ["init", "apply", "output"]


def test_existing_compartment_is_reused(home, monkeypatch):
    cloud = FakeCloud(compartments=["ocid1.compartment.oc1..old"])
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    make(cloud, home).up()
    assert not any(a[0][1:4] == ["iam", "compartment", "create"] for a in cloud.calls)


def test_no_quota_stops_before_creating(home, monkeypatch):
    cloud, tf = FakeCloud(quota={"AD-1": (1, 6), "AD-2": (0, 0)}), FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    with pytest.raises(VashError, match="No availability domain"):
        make(cloud, home).up()
    assert tf.calls == []


def test_capacity_error_moves_to_next_domain(home, monkeypatch):
    cloud, tf = FakeCloud(quota={"AD-1": (4, 24), "AD-2": (4, 24)}), FakeTerraform(capacity_fail={"AD-1"})
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    assert make(cloud, home).up() == 0
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["availability_domain"] == "AD-2"


def test_rerun_keeps_domain_and_image(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    make(FakeCloud(), home).up()
    later = FakeCloud(quota={"AD-1": (0, 0)}, images=("ocid1.image.oc1..newer",))
    assert make(later, home).up() == 0
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["image_id"] == "ocid1.image.oc1..u"
    assert not any(a[0][1:3] == ["limits", "resource-availability"] for a in later.calls)


def test_declined_confirmation_creates_nothing(home, monkeypatch):
    tf = FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    onboarding = make(FakeCloud(compartments=["ocid1.compartment..c"]), home)
    onboarding.confirm = lambda _q: False
    assert onboarding.up() == 1
    assert tf.calls == []


def test_runner_token_goes_through_stdin_only(home, monkeypatch):
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    make(cloud, home, runner_repo="owner/app").up(runner_token=lambda: "SECRET-TOKEN")
    register = [c for c in cloud.calls if c[0][0] == "ssh" and "config.sh" in c[0][-1]]
    assert len(register) == 1
    assert register[0][1]["input"] == "SECRET-TOKEN"
    assert "SECRET-TOKEN" not in " ".join(register[0][0])
    assert "https://github.com/owner/app" in register[0][0][-1]


def test_vm_not_ready_times_out(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    with pytest.raises(VashError, match="did not finish"):
        make(FakeCloud(ready=""), home, wait_minutes=1).up()


def test_missing_oci_cli(home):
    def missing(args, **kwargs):
        raise FileNotFoundError(args[0])
    with pytest.raises(AdapterNotInstalled):
        make(missing, home).up()


def test_down_without_state_does_nothing(home, monkeypatch):
    tf = FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    assert make(FakeCloud(), home).down() == 0
    assert tf.calls == []


def test_down_destroys(home, monkeypatch):
    tf = FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    onboarding = make(FakeCloud(), home)
    onboarding.up()
    assert onboarding.down() == 0
    assert tf.calls[-1][0][1] == "destroy"


def test_cli_unknown_cloud_is_not_available_yet(capsys):
    assert main(["onboard", "no-such-cloud"]) == 0
    assert "No onboarding" in capsys.readouterr().out


class FipsCloud(FakeCloud):
    """ssh-keygen refuses ed25519, as in OCI Cloud Shell (FIPS mode)."""

    def __call__(self, args, **kwargs):
        if args[0] == "ssh-keygen" and "ed25519" in args:
            self.calls.append((args, kwargs))
            return done(code=1, stderr="ED25519 keys are not allowed in FIPS mode")
        return super().__call__(args, **kwargs)


def test_fips_mode_falls_back_to_rsa(home, monkeypatch):
    cloud = FipsCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    assert make(cloud, home).up() == 0
    keygen = [c[0] for c in cloud.calls if c[0][0] == "ssh-keygen"]
    assert "rsa" in keygen[-1] and "4096" in keygen[-1]
    assert (home / ".ssh" / "north-key.pub").exists()


def test_existing_rsa_key_is_reused(home, monkeypatch):
    ssh = home / ".ssh"
    ssh.mkdir()
    (ssh / "id_rsa").write_text("private")
    (ssh / "id_rsa.pub").write_text("ssh-rsa AAAA mine")
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    make(cloud, home).up()
    assert not any(c[0][0] == "ssh-keygen" for c in cloud.calls)
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["ssh_public_key"] == "ssh-rsa AAAA mine"


SUBNET = "ocid1.subnet.oc1.me-jeddah-1..pub"


def test_existing_subnet_creates_no_network(home, monkeypatch):
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    assert make(cloud, home, subnet_id=SUBNET).up() == 0
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["subnet_id"] == SUBNET


def test_private_subnet_is_refused(home, monkeypatch):
    cloud = FakeCloud()
    cloud.subnet["prohibit-public-ip-on-vnic"] = True
    tf = FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    with pytest.raises(VashError, match="is private"):
        make(cloud, home, subnet_id=SUBNET).up()
    assert tf.calls == []


def test_subnet_without_ssh_rule_is_refused(home, monkeypatch):
    cloud = FakeCloud()
    cloud.ingress = [{"protocol": "6", "tcp-options": {"destination-port-range": {"min": 443, "max": 443}}}]
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    with pytest.raises(VashError, match="does not allow SSH"):
        make(cloud, home, subnet_id=SUBNET).up()


def test_new_compartment_needs_a_yes(home, monkeypatch):
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    onboarding = make(cloud, home)
    onboarding.confirm = lambda q: "Compartment" not in q
    with pytest.raises(VashError, match="No compartment"):
        onboarding.up()
    assert not any(c[0][1:4] == ["iam", "compartment", "create"] for c in cloud.calls)


def test_compartment_search_covers_subtree(home, monkeypatch):
    cloud = FakeCloud(compartments=["ocid1.compartment..kyc"])
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    make(cloud, home, compartment_name="KYC").up()
    listing = [c[0] for c in cloud.calls if c[0][1:4] == ["iam", "compartment", "list"]][0]
    assert "--compartment-id-in-subtree" in listing and "KYC" in listing


def test_names_are_typed_by_the_owner(home, monkeypatch):
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    answers = iter(["south", "kyc-runner"])  # prefix, compartment
    onboarding = make(cloud, home, name_prefix=None, compartment_name=None)
    onboarding.confirm = lambda q: "default" not in q
    onboarding.ask = lambda q, default: next(answers)
    onboarding.up()
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["name_prefix"] == "south"
    create = [c[0] for c in cloud.calls if c[0][1:4] == ["iam", "compartment", "create"]][0]
    assert "kyc-runner" in create


def test_empty_or_bad_name_is_asked_again_then_stops(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    onboarding = make(FakeCloud(), home, name_prefix=None)
    onboarding.confirm = lambda q: "default" not in q
    answers = iter(["", "Bad Name", "-x"])
    onboarding.ask = lambda q, default: next(answers)
    with pytest.raises(VashError, match="No valid answer"):
        onboarding.up()


def test_existing_key_needs_a_yes_else_new_key(home, monkeypatch):
    ssh = home / ".ssh"
    ssh.mkdir()
    (ssh / "id_rsa").write_text("private")
    (ssh / "id_rsa.pub").write_text("ssh-rsa AAAA mine")
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    onboarding = make(cloud, home)
    onboarding.confirm = lambda q: "existing SSH key" not in q
    onboarding.up()
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["ssh_public_key"] != "ssh-rsa AAAA mine"
    assert (ssh / "north-key.pub").exists() and (ssh / "id_rsa").read_text() == "private"


class UbuntuVm(FakeCloud):
    def __init__(self, os_id="ubuntu"):
        super().__init__()
        self.os_id = os_id

    def __call__(self, args, **kwargs):
        if args[0] == "ssh" and args[-1] == "cat /etc/os-release":
            self.calls.append((args, kwargs))
            return done(f'NAME="X"\nID={self.os_id}\n')
        return super().__call__(args, **kwargs)


def _key(home):
    ssh = home / ".ssh"
    ssh.mkdir(exist_ok=True)
    (ssh / "vm_key").write_text("private")
    return str(ssh / "vm_key")


def test_existing_vm_gets_installed_without_terraform(home, monkeypatch):
    cloud, tf = UbuntuVm(), FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    ob = make(cloud, home, vm_ip="203.0.113.9", vm_name="kyc-vm", ssh_user="ubuntu", ssh_key=_key(home),
              runner_repo="owner/app")
    assert ob.up(runner_token=lambda: "TOKEN") == 0
    assert tf.calls == []
    assert not any(c[0][0] == "oci" and c[0][2] in ("create",) for c in cloud.calls)
    start = [c for c in cloud.calls if c[0][0] == "ssh" and "vash-install.sh" in c[0][-1]][0]
    assert "@@" not in start[1]["input"] and 'RUN_USER="ubuntu"' in start[1]["input"]
    reg = [c for c in cloud.calls if c[0][0] == "ssh" and "config.sh" in c[0][-1]][0]
    assert "--name north-runner" in reg[0][-1]


def test_existing_vm_must_be_ubuntu_or_debian(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    ob = make(UbuntuVm("ol"), home, vm_ip="203.0.113.9", ssh_user="opc", ssh_key=_key(home))
    with pytest.raises(VashError, match="supports Ubuntu and Debian"):
        ob.up()


def test_existing_vm_needs_a_yes(home, monkeypatch):
    cloud = UbuntuVm()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    ob = make(cloud, home, vm_ip="203.0.113.9", ssh_user="ubuntu", ssh_key=_key(home))
    ob.confirm = lambda q: "Install VASH" not in q
    assert ob.up() == 1
    assert not any(c[0][0] == "ssh" and "vash-install.sh" in c[0][-1] for c in cloud.calls)


def test_yes_to_default_uses_vash_names(home, monkeypatch):
    cloud = FakeCloud()
    monkeypatch.setattr(tf_module.subprocess, "run", FakeTerraform())
    asked = []
    onboarding = make(cloud, home, name_prefix=None, compartment_name=None)
    onboarding.ask = lambda q, default: asked.append(q) or ""
    onboarding.up()
    assert asked == []  # the yes skipped typing
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["name_prefix"] == "vash"
    listing = [c[0] for c in cloud.calls if c[0][1:4] == ["iam", "compartment", "list"]][0]
    assert listing[listing.index("--name") + 1] == "vash"


def test_stops_after_cleanup_when_owner_says_no(home, monkeypatch):
    cloud, tf = FakeCloud(), FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    import vash.adapters.cloud.oci.inventory as inv_mod
    monkeypatch.setattr(inv_mod, "review", lambda *a, **k: inv_mod.Choice())
    ob = make(cloud, home, review=True)
    ob.confirm = lambda q: "Continue with the VASH VM setup" not in q
    assert ob.up() == 0
    assert tf.calls == []


def test_cleanup_only_never_builds(home, monkeypatch):
    tf = FakeTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    import vash.adapters.cloud.oci.inventory as inv_mod
    monkeypatch.setattr(inv_mod, "review", lambda *a, **k: inv_mod.Choice())
    assert make(FakeCloud(), home, review=True, cleanup_only=True).up() == 0
    assert tf.calls == []


def test_oci_error_shows_stdout_when_stderr_is_empty(home):
    def run(args, **kwargs):
        return done(stdout='{"code": "Conflict", "message": "boot volume in use"}', code=1)
    ob = make(run, home)
    with pytest.raises(VashError, match="boot volume in use"):
        ob.oci("compute", "instance", "terminate", "--instance-id", "x")


def test_cleanup_only_asks_for_no_vm_or_subnet(home, monkeypatch):
    import vash.adapters.cloud.oci.inventory as inv_mod
    seen = {}
    def fake_review(*a, **k):
        seen.update(k)
        return inv_mod.Choice()
    monkeypatch.setattr(inv_mod, "review", fake_review)
    assert make(FakeCloud(), home, review=True, cleanup_only=True).up() == 0
    assert seen == {"want_subnet": False, "want_vm": False}
