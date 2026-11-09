"""VASH check command."""
from pathlib import Path
from vash.tools.check_stack import run as check_stack_run

def run(repo_root: Path) -> int:
    """Run Stage 0 checks."""
    report = check_stack_run(repo_root)
    for c in report.checks:
        status = "OK" if c.ok else "FAIL"
        print(f"[{status}] {c.tool}: expected {c.expected}, found {c.found}")
    if report.problems:
        for p in report.problems:
            print(f"! {p}")
        return 1
    print("All clear.")
    return 0
