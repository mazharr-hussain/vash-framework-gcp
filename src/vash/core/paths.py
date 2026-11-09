"""VASH path resolution."""
import os
from pathlib import Path

DATA_DIRS = ("method", "catalog", "scaffold", "iac")


def vash_root() -> Path:
    """Return the VASH root: VASH_HOME, else the installed data, else the source checkout."""
    env = os.environ.get("VASH_HOME")
    if env:
        return Path(env).resolve()
    current = Path(__file__).resolve()
    data = current.parent.parent / "_data"
    if data.is_dir():
        return data
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "method").is_dir():
            return parent
    return Path.cwd()
