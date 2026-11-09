"""OCI cloud adapter running terraform."""
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping
from vash.core.interfaces import CloudAdapter, CloudPlan
from vash.core.exceptions import VashError, FreezeInvalid, AdapterNotInstalled

class Adapter(CloudAdapter):
    """OCI cloud adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.iac_dir = Path(self.settings.get("iac_dir", "iac/oci"))

    def _run_tf(self, environment: str, args: list[str]) -> str:
        env_dir = self.iac_dir / "environments" / environment
        if not env_dir.exists():
            raise VashError(f"Environment directory not found: {env_dir}", "Check iac_dir setting")
        cmd = ["terraform"] + args
        try:
            res = subprocess.run(cmd, cwd=env_dir, check=False, capture_output=True, text=True)
            if res.returncode not in (0, 2):
                raise VashError(
                    f"Terraform failed: {res.stderr}",
                    "Check terraform output and configuration"
                )
            return res.stdout
        except FileNotFoundError:
            raise AdapterNotInstalled(
                "terraform is not installed",
                "Install terraform and add it to PATH"
            )

    def plan(self, environment: str) -> CloudPlan:
        self._run_tf(environment, ["init", "-input=false"])
        out = self._run_tf(environment, ["plan", "-input=false", "-no-color", "-detailed-exitcode"])
        changes = 0
        for line in out.splitlines():
            if line.strip().startswith("Plan:"):
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and i + 1 < len(parts):
                        if parts[i+1].startswith("to"):
                            changes += int(p)
                break
        return CloudPlan(environment=environment, summary="Plan generated", changes=changes)

    def apply(self, environment: str, approved: bool) -> dict[str, Any]:
        if not approved:
            raise FreezeInvalid("Apply requires approval", "Set approved=True")
        self._run_tf(environment, ["init", "-input=false"])
        self._run_tf(environment, ["apply", "-input=false", "-auto-approve"])
        return self.outputs(environment)

    def destroy(self, environment: str, approved: bool) -> None:
        if not approved:
            raise FreezeInvalid("Destroy requires approval", "Set approved=True")
        self._run_tf(environment, ["init", "-input=false"])
        self._run_tf(environment, ["destroy", "-input=false", "-auto-approve"])

    def outputs(self, environment: str) -> dict[str, Any]:
        out = self._run_tf(environment, ["output", "-json"])
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {}
