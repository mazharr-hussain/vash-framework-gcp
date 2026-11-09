"""VASH load command."""
from pathlib import Path
from vash.loader.load import load

def run(repo_root: Path) -> int:
    """Run the clean-slate loader."""
    report = load(repo_root)
    for w in report.written:
        print(f"Wrote {w}")
    for r in report.removed:
        print(f"Removed {r}")
    for w in report.warnings:
        print(f"Warning: {w}")
    return 0
