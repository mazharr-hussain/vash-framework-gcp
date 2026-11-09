"""VASH status command."""
from pathlib import Path
from vash.core.freeze import load_freeze
from vash.core.exceptions import VashError

def run(repo_root: Path) -> int:
    """Show freeze and audit status."""
    try:
        freeze = load_freeze(repo_root)
    except VashError as e:
        print(f"Error: {e}")
        return 1

    print(f"Project: {freeze.data.get('project', {}).get('name', 'Unknown')}")
    print(f"Pack: {freeze.pack[0]} v{freeze.pack[1]}")
    print(f"Forge: {freeze.forge[0]}")
    print(f"CI: {freeze.ci[0]}")
    print(f"Cloud: {freeze.cloud[0]}")
    print(f"Floor: {freeze.floor}")

    audit_dir = repo_root / "audit" / "ava_logs"
    if audit_dir.exists():
        logs = list(audit_dir.glob("*.md"))
        print(f"\nAudit logs: {len(logs)}")
        for log in sorted(logs)[-5:]:
            print(f"  {log.name}")
    return 0
