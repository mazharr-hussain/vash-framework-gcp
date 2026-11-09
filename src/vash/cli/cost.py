"""VASH cost command."""
from pathlib import Path
from vash.core.exceptions import NotAvailableYet
from vash.core.freeze import load_freeze

def run(repo_root: Path) -> int:
    """Show cost meter status."""
    try:
        freeze = load_freeze(repo_root)
        routes = freeze.routes
        print("Configured LLM routes:")
        for name, r in routes.items():
            print(f"  {name}: {r.adapter} ({r.model})")
    except Exception:
        pass
    raise NotAvailableYet("cost meter", "The cost meter arrives in Wave 2")
