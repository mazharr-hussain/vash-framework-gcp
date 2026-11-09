"""Write guard (C-10) with fnmatch path validation."""
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Sequence

from vash.core.exceptions import WriteNotAllowed


def _check_allowed(path: Path, allowed_write: Sequence[str], repo_root: Path) -> Path:
    real_path = path.resolve()
    real_root = repo_root.resolve()
    try:
        rel = real_path.relative_to(real_root)
    except ValueError:
        raise WriteNotAllowed(
            f"Path {path} is outside repo root",
            "Only operate inside the project"
        )
    rel_str = str(rel).replace(os.sep, "/")
    matched = any(
        fnmatch(rel_str, pat) or fnmatch(rel_str, pat.rstrip("/") + "/**")
        for pat in allowed_write
    )
    if not matched:
        raise WriteNotAllowed(
            f"Path {rel_str} not in allowed_write",
            "Add pattern to paths.allowed_write"
        )
    return real_path


def guarded_write(path: Path, content: str, allowed_write: Sequence[str], repo_root: Path) -> Path:
    """Write path only if it matches an allowed glob."""
    real_path = _check_allowed(path, allowed_write, repo_root)
    real_path.parent.mkdir(parents=True, exist_ok=True)
    real_path.write_text(content, encoding="utf-8", newline="\n")
    return real_path


def guarded_delete(path: Path, allowed_write: Sequence[str], repo_root: Path) -> None:
    """Delete a file only if it matches an allowed glob. Never writes."""
    real_path = _check_allowed(path, allowed_write, repo_root)
    if not real_path.exists():
        raise WriteNotAllowed(f"Path does not exist: {path}", "Cannot delete missing path")
    if real_path.is_dir():
        raise WriteNotAllowed(f"Path is a directory: {path}", "Only delete files")
    real_path.unlink()
