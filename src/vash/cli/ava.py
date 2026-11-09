"""VASH ava command."""
from pathlib import Path
from vash.ava.runner import run_activity
from vash.core.freeze import load_freeze

def run(repo_root: Path, task_id: str) -> int:
    """Run one AvA activity."""
    try:
        freeze = load_freeze(repo_root)
    except Exception as e:
        print(f"Error loading freeze: {e}")
        return 1

    try:
        res = run_activity(task_id, repo_root)
        print(f"Activity {task_id}: {res.verdict} (score {res.scores[-1] if res.scores else 'N/A'})")
        for log in res.log_paths:
            print(f"Log: {log}")
        return 0 if res.verdict == "APPROVED" else 1
    except Exception as e:
        print(f"Error running AvA: {e}")
        return 1
