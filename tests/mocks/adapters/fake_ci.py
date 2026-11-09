"""Fake CI adapter for tests."""
from typing import Any, Mapping, Sequence
from pathlib import Path
from vash.core.interfaces import CIAdapter, RunRef, RunResult

class FakeCI(CIAdapter):
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.runs: dict[str, dict[str, Any]] = {}

    def start_run(self, workflow: str, ref: str, inputs: Mapping[str, str]) -> RunRef:
        run_id = f"fake-{len(self.runs) + 1}"
        self.runs[run_id] = {"status": "completed", "conclusion": "success"}
        return RunRef(run_id=run_id, url="fake")

    def get_run(self, run_id: str) -> RunResult:
        data = self.runs[run_id]
        return RunResult(run_id=run_id, status=data["status"], conclusion=data["conclusion"], url="fake")

    def register_runner(self, labels: Sequence[str]) -> str | None:
        return "fake-token"

    def install_hooks(self, repo_root: Path) -> list[Path]:
        return []
