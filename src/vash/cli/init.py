"""VASH init command."""
import shutil
from pathlib import Path
from vash.core.exceptions import VashError

def run(target: str, repo_root: Path) -> int:
    """Copy the scaffold to the target directory."""
    from vash.core.paths import vash_root
    target_path = Path(target).resolve()
    scaffold = vash_root() / "scaffold" / "project"
    if not scaffold.exists():
        raise VashError(
            f"Scaffold not found at {scaffold}",
            "Run this from the VASH checkout, or set VASH_HOME"
        )

    if target_path.exists() and any(target_path.iterdir()):
        raise VashError(
            f"Target directory {target_path} is not empty",
            "Choose an empty directory"
        )

    target_path.mkdir(parents=True, exist_ok=True)
    for item in scaffold.iterdir():
        if item.is_dir():
            shutil.copytree(item, target_path / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target_path / item.name)

    print(f"Initialised project in {target_path}")
    return 0
