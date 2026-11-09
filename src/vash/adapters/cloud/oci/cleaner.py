"""Oracle's compartment cleaner (oracle-devrel/oci-automation-hub, UPL-1.0), pinned and run by VASH.

The tool writes a dry-run plan, creates a Resource Manager discovery stack as a
backup, asks the operator to type DELETE, deletes in dependency order and checks
what is left. VASH fetches it at a pinned commit and runs it through
`cleaner_launch`, which adds Cloud Shell sign-in (delegation token).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

from vash.core.exceptions import AdapterNotInstalled, VashError

HUB_URL = "https://github.com/oracle-devrel/oci-automation-hub.git"
HUB_COMMIT = "685ae12a021874609d0125619580356ca904dbeb"
SAMPLE_DIR = "oci-compartment-cleaner-sample"
SDK_REQUIREMENT = "oci>=2.150,<3"


class Cleaner:
    def __init__(self, tools_dir: Path, region: str, echo: Callable[[str], None],
                 run: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.tools_dir = tools_dir
        self.region = region
        self.echo = echo
        self._run = run

    def _check(self, args: list[str], what: str) -> None:
        try:
            res = self._run(args, check=False, capture_output=True, text=True)
        except FileNotFoundError:
            raise AdapterNotInstalled(f"{args[0]} is not installed", f"Install {args[0]} to {what}")
        if res.returncode != 0:
            raise VashError(f"Could not {what}: {res.stderr.strip()[-300:]}", "Check the network and run again")

    def ensure(self) -> Path:
        """The cleaner at the pinned commit, and the OCI Python SDK it needs."""
        repo = self.tools_dir / "oci-automation-hub"
        if not (repo / ".git").exists():
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            self.echo(f"Fetching Oracle's compartment cleaner ({HUB_COMMIT[:12]}) ...")
            self._check(["git", "clone", "-q", "--filter=blob:none", HUB_URL, str(repo)], "download the cleaner")
        self._check(["git", "-C", str(repo), "checkout", "-q", HUB_COMMIT], "pin the cleaner")
        self._check([sys.executable, "-m", "pip", "install", "-q", SDK_REQUIREMENT], "install the OCI Python SDK")
        return repo / SAMPLE_DIR

    def command(self, compartment_id: str, backup_compartment_id: str, execute: bool,
                region: str | None = None) -> list[str]:
        sample = self.ensure()
        args = [sys.executable, "-m", "vash.adapters.cloud.oci.cleaner_launch", str(sample),
                "--compartment-id", compartment_id, "--region", region or self.region, "--auth", "config",
                "--output-dir", str(self.tools_dir / "cleaner-runs")]
        if execute:
            args += ["--execute", "--rm-backup-stack-compartment-id", backup_compartment_id,
                     "--rm-backup-failure-action", "stop"]
        else:
            args += ["--dry-run-only"]
        return args

    def run(self, compartment_id: str, backup_compartment_id: str, execute: bool, region: str | None = None) -> int:
        """Runs in the terminal, so the tool's own DELETE question reaches the owner."""
        return self._run(self.command(compartment_id, backup_compartment_id, execute, region), check=False).returncode
