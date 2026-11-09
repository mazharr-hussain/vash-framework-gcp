"""One-command onboarding on OCI: find quota, create the Always Free runner VM, install VASH on it.

Meant to run in OCI Cloud Shell, where the oci CLI and terraform are already signed in.
Every OCI call goes through the oci CLI with an argument list; every terraform call goes
through the cloud Adapter of this package.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from vash.core.exceptions import AdapterNotInstalled, VashError
from vash.core.paths import vash_root

from .adapter import Adapter

SHAPE = "VM.Standard.A1.Flex"
ENVIRONMENT = "always-free"
DEFAULT_SOURCE = "git+https://github.com/mazharr-hussain/vash-framework.git"
DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_NAME = "vash"
COMPARTMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
NAME_PREFIX_RE = re.compile(r"^[a-z][a-z0-9-]{0,19}$")
CLOUD_INIT_NAME = "vash-runner.sh"
CAPACITY_ERRORS = ("out of host capacity", "outofhostcapacity", "out of capacity")

Runner = Callable[..., subprocess.CompletedProcess]


@dataclass
class Options:
    """What the user chose on the command line."""

    compartment_name: str | None = None
    subnet_id: str | None = None
    review: bool = False  # interactive inventory, never with --yes
    cleanup_only: bool = False
    name_prefix: str | None = None  # display names of new objects: <prefix>-runner, <prefix>-vcn ...
    vm_ip: str | None = None  # an existing VM to install VASH on (no terraform)
    vm_name: str = ""
    ssh_user: str | None = None
    ssh_key: str | None = None
    ocpus: int = 2
    memory_in_gbs: int = 12
    os_name: str = "Canonical Ubuntu"
    os_version: str = "24.04"
    admin_cidr: str | None = None
    workdir: Path = field(default_factory=lambda: Path.home() / ".vash" / "oci")
    vash_source: str = DEFAULT_SOURCE
    model: str = DEFAULT_MODEL
    runner_repo: str | None = None
    wait_minutes: int = 30


def _allows_ssh(rule: dict) -> bool:
    proto = str(rule.get("protocol", ""))
    if proto == "all":
        return True
    if proto != "6":
        return False
    tcp = rule.get("tcp-options") or {}
    ports = tcp.get("destination-port-range")
    if not ports:
        return True
    return int(ports.get("min", 0)) <= 22 <= int(ports.get("max", 0))


class Onboarding:
    """The onboarding steps; each one prints what it found."""

    def __init__(
        self,
        options: Options,
        run: Runner = subprocess.run,
        echo: Callable[[str], None] = print,
        confirm: Callable[[str], bool] | None = None,
        ask: Callable[[str, str], str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        env: dict[str, str] | None = None,
    ):
        self.options = options
        self._run = run
        self.echo = echo
        self.confirm = confirm or (lambda _question: True)
        self.ask = ask or (lambda _question, default: default)
        self.sleep = sleep
        self.env = dict(os.environ if env is None else env)

    # ---- helpers -------------------------------------------------------
    def _cmd(self, args: Sequence[str], stdin: str | None = None) -> subprocess.CompletedProcess:
        try:
            return self._run(list(args), check=False, capture_output=True, text=True, input=stdin)
        except FileNotFoundError:
            raise AdapterNotInstalled(f"{args[0]} is not installed", f"Install {args[0]}, or run this in OCI Cloud Shell")

    def oci(self, *args: str) -> Any:
        res = self._cmd(["oci", *args, "--output", "json"])
        if res.returncode != 0:
            detail = (res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}")[-1500:]
            raise VashError(f"oci {' '.join(args[:3])} failed: {detail}", "Check the OCI policy and the oci CLI setup")
        out = res.stdout.strip()
        return json.loads(out) if out else {}

    # ---- discovery -----------------------------------------------------
    def in_cloud_shell(self) -> bool:
        return self.env.get("OCI_CLI_CLOUD_SHELL", "").lower() == "true"

    def tenancy_and_region(self) -> tuple[str, str]:
        tenancy = self.env.get("OCI_TENANCY") or self.env.get("OCI_CLI_TENANCY")
        region = self.env.get("OCI_REGION") or self.env.get("OCI_CLI_REGION")
        if not (tenancy and region):
            cfg = Path(self.env.get("OCI_CONFIG_FILE", str(Path.home() / ".oci" / "config")))
            if cfg.exists():
                for line in cfg.read_text().splitlines():
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if key == "tenancy" and not tenancy:
                        tenancy = value
                    if key == "region" and not region:
                        region = value
        if not (tenancy and region):
            raise VashError("Tenancy or region not found", "Run in OCI Cloud Shell, or run `oci setup config` first")
        return tenancy, region

    def compartment_name(self) -> str:
        """The name from --compartment, else asked (Enter keeps the default)."""
        if not self.options.compartment_name:
            self.options.compartment_name = self.choose_name(
                "compartment", "Compartment for the VM (an existing name, or a new one to create)",
                COMPARTMENT_RE, "letters, digits, '.', '-' and '_', at most 100")
        return self.options.compartment_name

    def ensure_compartment(self, tenancy: str) -> str:
        name = self.compartment_name()
        found = self.oci("iam", "compartment", "list", "--compartment-id", tenancy, "--name", name,
                         "--lifecycle-state", "ACTIVE", "--compartment-id-in-subtree", "true",
                         "--access-level", "ACCESSIBLE")
        items = found.get("data", []) if isinstance(found, dict) else []
        if items:
            self.echo(f"Compartment '{name}' exists")
            return items[0]["id"]
        if not self.confirm(f"Compartment '{name}' does not exist. Create it?"):
            raise VashError(f"No compartment '{name}'", "Pass --compartment <name of an existing compartment>")
        created = self.oci("iam", "compartment", "create", "--compartment-id", tenancy, "--name", name,
                           "--description", "VASH runner (created by vash onboard)",
                           "--wait-for-state", "ACTIVE")
        self.echo(f"Compartment '{name}' created")
        return created["data"]["id"]

    def check_subnet(self, subnet_id: str) -> None:
        """An existing subnet must be public and let SSH in; VASH never changes it."""
        subnet = self.oci("network", "subnet", "get", "--subnet-id", subnet_id).get("data", {})
        if subnet.get("prohibit-public-ip-on-vnic", True):
            raise VashError(f"Subnet {subnet.get('display-name', subnet_id)} is private",
                            "Pass --subnet-id of a public subnet")
        for sl_id in subnet.get("security-list-ids", []):
            rules = self.oci("network", "security-list", "get", "--security-list-id", sl_id).get("data", {})
            for rule in rules.get("ingress-security-rules", []):
                if _allows_ssh(rule):
                    self.echo(f"Using subnet {subnet.get('display-name', subnet_id)}; no network is created")
                    return
        raise VashError(
            f"Subnet {subnet.get('display-name', subnet_id)} does not allow SSH (TCP 22)",
            "Add an ingress rule TCP 22 from your IP to its security list, then run again",
        )

    def availability_domains(self, tenancy: str) -> list[str]:
        data = self.oci("iam", "availability-domain", "list", "--compartment-id", tenancy).get("data", [])
        return [ad["name"] for ad in data]

    def _available(self, tenancy: str, ad: str, limit: str) -> float:
        data = self.oci("limits", "resource-availability", "get", "--service-name", "compute",
                        "--limit-name", limit, "--compartment-id", tenancy, "--availability-domain", ad).get("data", {})
        value = data.get("available")
        return float(value) if value is not None else 0.0

    def domains_with_quota(self, tenancy: str) -> list[str]:
        fits = []
        for ad in self.availability_domains(tenancy):
            cores = self._available(tenancy, ad, "standard-a1-core-count")
            memory = self._available(tenancy, ad, "standard-a1-memory-count")
            ok = cores >= self.options.ocpus and memory >= self.options.memory_in_gbs
            self.echo(f"{ad}: {cores:g} A1 cores, {memory:g} GB free{'' if ok else ' (not enough)'}")
            if ok:
                fits.append(ad)
        if not fits:
            raise VashError(
                f"No availability domain has {self.options.ocpus} A1 cores and {self.options.memory_in_gbs} GB free",
                "Free A1 quota (stop or delete A1 instances), or pass --ocpus/--memory smaller values",
            )
        return fits

    def latest_image(self, compartment: str) -> str:
        data = self.oci("compute", "image", "list", "--compartment-id", compartment,
                        "--operating-system", self.options.os_name,
                        "--operating-system-version", self.options.os_version,
                        "--shape", SHAPE, "--sort-by", "TIMECREATED", "--sort-order", "DESC",
                        "--limit", "1").get("data", [])
        if not data:
            raise VashError(f"No {self.options.os_name} {self.options.os_version} image for {SHAPE}",
                            "Pass --os-version with a version OCI offers for Arm")
        self.echo(f"Image: {data[0].get('display-name', data[0]['id'])}")
        return data[0]["id"]

    def _state(self) -> dict[str, Any]:
        path = self.options.workdir / "onboard.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def _save_state(self, **values: Any) -> None:
        path = self.options.workdir / "onboard.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**self._state(), **values}, indent=2) + "\n")

    def ssh_public_key(self) -> tuple[Path, str]:
        """The owner chooses: an existing key, or a new one (never overwriting a file).

        A VM built earlier keeps its key: a new key would make terraform replace the VM.
        """
        kept = self._state().get("ssh_key")
        if kept and Path(kept).exists() and Path(kept + ".pub").exists():
            return Path(kept), Path(kept + ".pub").read_text().strip()
        ssh_dir = Path.home() / ".ssh"
        for key in sorted(ssh_dir.glob("*.pub")) if ssh_dir.is_dir() else []:
            private = key.with_suffix("")
            if private.exists() and self.confirm(f"Use the existing SSH key {private}?"):
                self._save_state(ssh_key=str(private))
                return private, key.read_text().strip()
        ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        base = f"{self.prefix or 'vash-vm'}-key"
        key = ssh_dir / base
        n = 2
        while key.exists() or Path(str(key) + ".pub").exists():
            key, n = ssh_dir / f"{base}-{n}", n + 1
        errors = []
        for args in (["-t", "ed25519"], ["-t", "rsa", "-b", "4096"]):
            res = self._cmd(["ssh-keygen", "-q", *args, "-N", "", "-f", str(key)])
            if res.returncode == 0 and Path(str(key) + ".pub").exists():
                self.echo(f"SSH key created: {key}")
                self._save_state(ssh_key=str(key))
                return key, Path(str(key) + ".pub").read_text().strip()
            errors.append(f"{args[1]}: {res.stderr.strip()}")
        raise VashError(f"ssh-keygen failed: {'; '.join(errors)}",
                        f"Create a key with: ssh-keygen -t rsa -b 4096 -N '' -f {key}")

    def admin_cidr(self) -> str:
        if self.options.admin_cidr:
            return self.options.admin_cidr
        try:
            with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10) as resp:
                ip = resp.read().decode().strip()
        except OSError as exc:
            raise VashError(f"Could not find this shell's public IP: {exc}", "Pass --admin-cidr x.x.x.x/32")
        return f"{ip}/32"

    # ---- infrastructure --------------------------------------------------
    def prepare_workdir(self) -> Path:
        """Copy the IaC to a work folder that keeps the terraform state between runs."""
        src = vash_root() / "iac" / "oci"
        if not src.is_dir():
            raise VashError(f"IaC not found at {src}", "Reinstall VASH, or set VASH_HOME to a checkout")
        dest = self.options.workdir
        for item in src.rglob("*"):
            if item.is_file() and ".terraform" not in item.parts:
                target = dest / item.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        return dest

    def user_data(self, workdir: Path) -> str:
        text = (workdir / "cloud-init" / "vash-runner.sh").read_text()
        return (text.replace("@@VASH_SOURCE@@", self.options.vash_source)
                .replace("@@MODEL@@", self.options.model).replace("@@RUN_USER@@", self.user))

    def write_cloud_init(self, workdir: Path) -> str:
        """The CD3 instance module reads scripts/<name> beside the environment; it must exist before plan."""
        scripts = workdir / "environments" / ENVIRONMENT / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (scripts / CLOUD_INIT_NAME).write_text(self.user_data(workdir))
        return CLOUD_INIT_NAME

    def tfvars_path(self, workdir: Path) -> Path:
        return workdir / "environments" / ENVIRONMENT / "terraform.tfvars.json"

    def existing_tfvars(self) -> dict[str, Any]:
        path = self.tfvars_path(self.options.workdir)
        return json.loads(path.read_text()) if path.exists() else {}

    def write_tfvars(self, workdir: Path, values: dict[str, Any]) -> None:
        path = self.tfvars_path(workdir)
        path.write_text(json.dumps(values, indent=2) + "\n")
        path.chmod(0o600)

    def create(self, workdir: Path, base: dict[str, Any], domains: list[str]) -> dict[str, Any]:
        adapter = Adapter({"iac_dir": str(workdir)})
        last: VashError | None = None
        for ad in domains:
            self.write_tfvars(workdir, {**base, "availability_domain": ad})
            self.echo(f"Creating the VM in {ad} ...")
            try:
                return adapter.apply(ENVIRONMENT, approved=True)
            except VashError as exc:
                if not any(word in str(exc).lower() for word in CAPACITY_ERRORS):
                    raise
                self.echo(f"{ad}: out of host capacity, trying the next domain")
                last = exc
        raise VashError(f"Every availability domain is out of A1 capacity: {last}",
                        "Run `vash onboard oci` again later; free A1 capacity comes and goes")

    # ---- the VM --------------------------------------------------------
    def choose_name(self, what: str, question: str, check: "re.Pattern[str]", rule: str) -> str:
        """Default 'vash' after a yes; otherwise the owner types the name."""
        if self.confirm(f"Use the default {what} '{DEFAULT_NAME}'?"):
            return DEFAULT_NAME
        return self.ask_required(question, check, rule)

    def ask_required(self, question: str, check: "re.Pattern[str]", rule: str) -> str:
        """Typed by the owner; no default. Asked up to 3 times."""
        for _ in range(3):
            answer = self.ask(question, "").strip()
            if answer and check.match(answer):
                return answer
            self.echo(f"Please type a name: {rule}")
        raise VashError(f"No valid answer to: {question}", f"Run again and type a name ({rule}), or pass it as an option")

    @property
    def user(self) -> str:
        return self.options.ssh_user or "ubuntu"

    @property
    def runner_name(self) -> str:
        base = self.prefix or re.sub(r"[^a-z0-9-]+", "-", self.options.vm_name.lower()).strip("-") or "vm"
        return f"{base}-runner"

    @property
    def prefix(self) -> str:
        return self.options.name_prefix or ""

    def ssh(self, key: Path, ip: str, command: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return self._cmd(["ssh", "-i", str(key), "-o", "StrictHostKeyChecking=accept-new",
                          "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", f"{self.user}@{ip}", command], stdin=stdin)

    def wait_ready(self, key: Path, ip: str) -> str:
        deadline = self.options.wait_minutes * 60
        waited = 0
        while waited <= deadline:
            res = self.ssh(key, ip, "cat /var/lib/vash/ready")
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            self.sleep(30)
            waited += 30
        raise VashError(f"The VM did not finish installing in {self.options.wait_minutes} minutes",
                        f"ssh {self.user}@{ip} and read /var/log/vash-onboard.log")

    def register_runner(self, key: Path, ip: str, token: str) -> None:
        repo = self.options.runner_repo
        command = (
            "cd ~/actions-runner && "
            f"./config.sh --unattended --replace --url https://github.com/{repo} "
            f"--name {self.runner_name} --labels self-hosted,vash --token \"$(cat)\" && "
            f"sudo ./svc.sh install {self.user} && sudo ./svc.sh start"
        )
        res = self.ssh(key, ip, command, stdin=token)
        if res.returncode != 0:
            raise VashError(f"Runner registration failed: {res.stderr.strip()[-300:]}",
                            "Get a new token (it expires after 1 hour) and run `vash onboard oci --runner-repo` again")
        self.echo(f"GitHub runner registered for {repo}")

    # ---- entry points --------------------------------------------------
    def up(self, runner_token: Callable[[], str] | None = None) -> int:
        tenancy, region = self.tenancy_and_region()
        self.echo(f"Tenancy found, region {region}{' (Cloud Shell)' if self.in_cloud_shell() else ''}")
        if self.options.review:
            from .cleaner import Cleaner
            from .inventory import Inventory, review
            cleaner = Cleaner(self.options.workdir.parent / "tools", region, self.echo)
            choice = review(Inventory(self.oci, self.echo, cleaner, sleep=self.sleep), tenancy, self.confirm, self.ask,
                            want_subnet=(not self.options.cleanup_only and not self.options.subnet_id
                                         and not self.existing_tfvars().get("subnet_id")),
                            want_vm=not self.options.cleanup_only and not self.options.vm_ip
                            and not self.existing_tfvars())
            if choice.vm is not None:
                self.options.vm_ip, self.options.vm_name = choice.vm.public, choice.vm.name
            elif choice.subnet_id:
                self.options.subnet_id = choice.subnet_id
        if self.options.cleanup_only:
            self.echo("Cleanup finished; no VM setup (--cleanup-only)")
            return 0
        if self.options.review and not self.confirm("Continue with the VASH VM setup now?"):
            self.echo("Stopped after the cleanup; nothing else was changed")
            return 0
        if self.options.vm_ip:
            return self.install_on_existing(runner_token)
        previous = self.existing_tfvars()
        if previous.get("name_prefix"):
            self.options.name_prefix = previous["name_prefix"]  # keep the names terraform already manages
        elif not self.options.name_prefix:
            self.options.name_prefix = self.choose_name(
                "name prefix", "Name prefix for the new objects, e.g. north, south or your name (VM: <prefix>-runner, network: <prefix>-vcn)",
                NAME_PREFIX_RE, "lowercase letters, digits and hyphens, starting with a letter, at most 20")
        if not NAME_PREFIX_RE.match(self.prefix):
            raise VashError(f"Invalid name prefix '{self.prefix}'", "Use lowercase letters, digits and hyphens, max 20")
        compartment = self.ensure_compartment(tenancy)
        if previous:
            # A VM made earlier keeps its domain and image, so terraform repairs it instead of replacing it.
            self.echo(f"Earlier onboarding found in {self.options.workdir}; checking that VM")
            domains = [previous["availability_domain"]]
            image = previous["image_id"]
        else:
            domains = self.domains_with_quota(tenancy)
            image = self.latest_image(compartment)
        subnet_id = self.options.subnet_id or previous.get("subnet_id", "")
        if subnet_id:
            self.check_subnet(subnet_id)
        key, public_key = self.ssh_public_key()
        cidr = self.admin_cidr()
        if not subnet_id:
            self.echo(f"SSH will be open to {cidr} only")
        if not self.confirm(f"Create a {self.options.ocpus}-core {self.options.memory_in_gbs} GB Always Free VM in {region}?"):
            self.echo("Stopped; nothing was created")
            return 1
        workdir = self.prepare_workdir()
        base = {
            "region": region,
            "compartment_id": compartment,
            "image_id": image,
            "admin_cidr": cidr,
            "subnet_id": subnet_id,
            "ssh_public_key": public_key,
            "oci_auth": "InstancePrincipal" if self.in_cloud_shell() else "ApiKey",
            "ocpus": self.options.ocpus,
            "memory_in_gbs": self.options.memory_in_gbs,
            "cloud_init_script": self.write_cloud_init(workdir),
            "name_prefix": self.prefix,
        }
        outputs = self.create(workdir, base, domains)
        ip = outputs.get("runner_ip", {}).get("value")
        if not ip:
            raise VashError("The VM has no public IP", f"Check the instance in compartment '{self.options.compartment_name}'")
        self.echo(f"VM is up at {ip}; installing VASH, terraform and Ollama (about 10-20 minutes) ...")
        ready = self.wait_ready(key, ip)
        self.echo(ready)
        if self.options.runner_repo and runner_token is not None:
            self.register_runner(key, ip, runner_token())
        self.echo(f"Done. Connect with: ssh -i {key} {self.user}@{ip}")
        return 0

    def install_on_existing(self, runner_token: Callable[[], str] | None = None) -> int:
        """Install VASH on a VM that already exists: nothing is created in OCI, no terraform."""
        ip, name = self.options.vm_ip, self.options.vm_name or self.options.vm_ip
        if not self.options.ssh_user:
            self.options.ssh_user = self.ask(f"SSH user on {name}", "ubuntu").strip() or "ubuntu"
        key_text = self.options.ssh_key or self.ask(f"Private key for {name}", "~/.ssh/id_rsa").strip() or "~/.ssh/id_rsa"
        key = Path(key_text).expanduser()
        if not key.exists():
            raise VashError(f"Key {key} not found", f"Copy the private key of {name} to Cloud Shell, or pass --ssh-key")
        res = self.ssh(key, ip, "cat /etc/os-release")
        if res.returncode != 0:
            raise VashError(f"SSH to {self.user}@{ip} failed: {res.stderr.strip()[-200:]}",
                            "Check the key, the user, and that the VM's security list allows TCP 22 from this shell")
        os_id = next((line.split("=", 1)[1].strip('"') for line in res.stdout.splitlines()
                      if line.startswith("ID=")), "")
        if os_id not in ("ubuntu", "debian"):
            raise VashError(f"{name} runs '{os_id or 'unknown'}'; the installer supports Ubuntu and Debian",
                            "Pick an Ubuntu VM, or create a new one (Enter at the VM question)")
        if not self.confirm(f"Install VASH, terraform, Ollama and the runner files on {name} ({ip})? This changes that VM"):
            self.echo("Stopped; nothing was changed")
            return 1
        script = self.user_data(self.prepare_workdir())
        res = self.ssh(key, ip, "cat > /tmp/vash-install.sh && sudo nohup bash /tmp/vash-install.sh >/dev/null 2>&1 &",
                       stdin=script)
        if res.returncode != 0:
            raise VashError(f"Could not start the installer on {name}: {res.stderr.strip()[-200:]}",
                            f"ssh {self.user}@{ip} and check that the user may run sudo")
        self.echo(f"Installing on {name} (about 10-20 minutes) ...")
        self.echo(self.wait_ready(key, ip))
        if self.options.runner_repo and runner_token is not None:
            self.register_runner(key, ip, runner_token())
        self.echo(f"Done. Connect with: ssh -i {key} {self.user}@{ip}")
        return 0

    def down(self) -> int:
        workdir = self.options.workdir
        if not self.tfvars_path(workdir).exists():
            self.echo(f"Nothing to remove: no onboarding state in {workdir}")
            return 0
        if not self.confirm("Destroy the VASH VM and its network?"):
            self.echo("Stopped; nothing was removed")
            return 1
        Adapter({"iac_dir": str(workdir)}).destroy(ENVIRONMENT, approved=True)
        self.echo("VASH VM and network removed")
        return 0


def run_cli(args: Any) -> int:
    """Entry point for `vash onboard oci`."""
    import getpass

    options = Options(
        compartment_name=args.compartment,
        subnet_id=args.subnet_id,
        ocpus=args.ocpus,
        memory_in_gbs=args.memory,
        os_version=args.os_version,
        admin_cidr=args.admin_cidr,
        runner_repo=args.runner_repo,
        model=args.model,
        review=(not args.yes and not args.no_inventory) or args.cleanup_only,
        cleanup_only=args.cleanup_only,
        name_prefix=args.name_prefix,
        vm_ip=args.vm_ip,
        ssh_user=args.ssh_user,
        ssh_key=args.ssh_key,
    )
    if args.workdir:
        options.workdir = Path(args.workdir)

    def ask(question: str) -> bool:
        if args.yes:
            return True
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")

    def ask_text(question: str, default: str) -> str:
        if args.yes:
            return default
        return input(f"{question} [{default}]: " if default else f"{question}: ")

    def token() -> str:
        return getpass.getpass(f"GitHub runner registration token for {args.runner_repo} (not stored): ").strip()

    onboarding = Onboarding(options, confirm=ask, ask=ask_text)
    if args.down:
        return onboarding.down()
    return onboarding.up(runner_token=token if args.runner_repo else None)
