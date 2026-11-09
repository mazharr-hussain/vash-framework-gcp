"""Ship method/, catalog/ and scaffold/ inside the wheel as vash/_data."""
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

DATA_DIRS = ("method", "catalog", "scaffold", "iac")


class BuildWithData(build_py):
    def run(self):
        super().run()
        if getattr(self, "editable_mode", False):
            return
        root = Path(__file__).resolve().parent
        target = Path(self.build_lib) / "vash" / "_data"
        for name in DATA_DIRS:
            dest = target / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(root / name, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


setup(cmdclass={"build_py": BuildWithData})
