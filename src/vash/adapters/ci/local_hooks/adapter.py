"""Local git hooks CI adapter with no network and $0 cost."""
import shutil
import stat
import time
from typing import Any, Mapping, Sequence
from pathlib import Path
from vash.core.interfaces import CIAdapter, RunRef, RunResult
from vash.core.exceptions import VashError, NotAvailableYet
from vash.core.paths import vash_root
import subprocess

class Adapter(CIAdapter):
    """Local git hooks CI adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.commands = self.settings.get("commands", [])
        self._runs: dict[str, dict[str, Any]] = {}
        self._counter = 0

    def start_run(self, workflow: str, ref: str, inputs: Mapping[str, str]) -> RunRef:
        self._counter += 1
        run_id = f"local-{time.time_ns()}-{self._counter}"
        self._runs[run_id] = {"status": "in_progress", "conclusion": None}
        success = True
        for cmd in self.commands:
            try:
                res = subprocess.run(cmd, check=False, capture_output=True)
                if res.returncode != 0:
                    success = False
                    break
            except OSError as e:
                raise VashError(f"Failed to run command {cmd}: {e}", "Check the command in settings")
        self._runs[run_id] = {
            "status": "completed",
            "conclusion": "success" if success else "failure"
        }
        return RunRef(run_id=run_id, url="")

    def get_run(self, run_id: str) -> RunResult:
        if run_id not in self._runs:
            raise VashError(f"Run {run_id} not found", "Check run ID")
        data = self._runs[run_id]
        return RunResult(
            run_id=run_id, status=data["status"], conclusion=data["conclusion"], url=""
        )

    def register_runner(self, labels: Sequence[str]) -> str | None:
        return None

    def install_hooks(self, repo_root: Path) -> list[Path]:
        src_dir = vash_root() / "catalog" / "ci" / "local-hooks" / "hooks"
        if not src_dir.exists():
            raise NotAvailableYet(
                f"Hooks directory not found: {src_dir}",
                "The catalog step (Step 7) will provide local-hooks"
            )
        git_hooks_dir = repo_root / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for src_file in src_dir.iterdir():
            if not src_file.is_file():
                continue
            dst_file = git_hooks_dir / src_file.name
            shutil.copy2(src_file, dst_file)
            dst_file.chmod(dst_file.stat().st_mode | stat.S_IEXEC)
            written.append(dst_file)
        return written
