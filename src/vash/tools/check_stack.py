"""Stage 0: ownership and dependency check (C-12)."""
import sys
import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from vash.core.freeze import load_freeze, load_stack_pack
from vash.core.interfaces import VersionCheck, StackPack
from vash.core.exceptions import VashError, FreezeInvalid
from vash.core.paths import vash_root

@dataclass(frozen=True)
class StageReport:
    checks: list[VersionCheck]
    problems: list[str]
    ok: bool

class CatalogStackPack(StackPack):
    """Reads a stack pack from the catalog."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.repo_root = Path(settings.get("repo_root", "."))
        self.pack_id = settings.get("pack_id", "")

    def manifest(self) -> dict[str, Any]:
        return load_stack_pack(self.repo_root, self.pack_id)

    def check_versions(self) -> list[VersionCheck]:
        data = self.manifest()
        checks = []
        for tool in data.get("tools", []):
            cmd = tool.get("version_command", [])
            expected = tool.get("version", "")
            if not cmd:
                checks.append(VersionCheck(tool["id"], expected, None, False))
                continue
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                found = res.stdout.strip() if res.returncode == 0 else None
                ok = found is not None and expected in found
                checks.append(VersionCheck(tool["id"], expected, found, ok))
            except FileNotFoundError:
                checks.append(VersionCheck(tool["id"], expected, None, False))
        return checks

    def outputs_layout(self) -> list[str]:
        return self.manifest().get("outputs", [])

def run(repo_root: Path) -> StageReport:
    """Run Stage 0 checks on the repository."""
    problems = []
    checks = []

    try:
        freeze = load_freeze(repo_root)
    except VashError as e:
        return StageReport(checks=[], problems=[str(e)], ok=False)

    pack_id = freeze.pack[0]
    try:
        pack_data = load_stack_pack(repo_root, pack_id)
    except VashError as e:
        problems.append(f"Stack pack {pack_id} invalid: {e}")
        return StageReport(checks=[], problems=problems, ok=False)

    pack = CatalogStackPack({"repo_root": repo_root, "pack_id": pack_id})
    checks.extend(pack.check_versions())
    for c in checks:
        if not c.ok:
            problems.append(f"Tool {c.tool} expected {c.expected}, found {c.found}")

    for adr_id in freeze.decisions:
        matches = list((repo_root / "decisions").glob(f"{adr_id}*.md"))
        if not matches:
            problems.append(f"ADR {adr_id} listed in freeze but not found in decisions/")
            continue
        content = matches[0].read_text(encoding="utf-8")
        if "## Status\nACCEPTED" not in content and "## Status\r\nACCEPTED" not in content:
            problems.append(f"ADR {adr_id} is not ACCEPTED")

    return StageReport(checks=checks, problems=problems, ok=len(problems) == 0)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VASH Stage 0 check")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    report = run(args.repo)

    print("Stage 0: Freeze and Stack Check")
    for c in report.checks:
        status = "OK" if c.ok else "FAIL"
        print(f"[{status}] {c.tool}: expected {c.expected}, found {c.found}")

    if report.problems:
        print("\nProblems found:")
        for p in report.problems:
            print(f"! {p}")
        return 1

    print("\nAll clear.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
