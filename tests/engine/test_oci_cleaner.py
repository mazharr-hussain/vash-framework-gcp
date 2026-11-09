import subprocess
import sys

from vash.adapters.cloud.oci import cleaner_launch
from vash.adapters.cloud.oci.cleaner import HUB_COMMIT, Cleaner


def ok(*a, **k):
    return subprocess.CompletedProcess([], 0, stdout="", stderr="")


def test_command_pins_the_commit_and_keeps_dry_run_default(tmp_path):
    calls = []
    def run(args, **k):
        calls.append(args)
        return ok()
    c = Cleaner(tmp_path, "me-jeddah-1", lambda m: None, run=run)
    dry = c.command("ocid1.compartment..p", "ocid1.tenancy..t", execute=False)
    assert any(HUB_COMMIT in a for a in calls[1])  # git checkout <pinned commit>
    assert "--dry-run-only" in dry and "--execute" not in dry
    real = c.command("ocid1.compartment..p", "ocid1.tenancy..t", execute=True)
    assert "--execute" in real
    assert real[real.index("--rm-backup-stack-compartment-id") + 1] == "ocid1.tenancy..t"
    assert real[real.index("--rm-backup-failure-action") + 1] == "stop"
    assert real[:3] == [sys.executable, "-m", "vash.adapters.cloud.oci.cleaner_launch"]


def test_cloud_shell_token_read_from_config(tmp_path, monkeypatch):
    token = tmp_path / "delegation_token"
    token.write_text("TOKEN-VALUE\n")
    cfg = tmp_path / "config"
    cfg.write_text(f"[DEFAULT]\nregion=me-jeddah-1\ndelegation_token_file={token}\n")
    monkeypatch.setenv("OCI_CLI_CLOUD_SHELL", "True")
    monkeypatch.setenv("OCI_CONFIG_FILE", str(cfg))
    assert cleaner_launch._cloud_shell_token() == "TOKEN-VALUE"
    monkeypatch.setenv("OCI_CLI_CLOUD_SHELL", "False")
    assert cleaner_launch._cloud_shell_token() is None
