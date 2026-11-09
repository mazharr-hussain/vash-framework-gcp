"""VASH package."""
import importlib.metadata
try:
    __version__ = importlib.metadata.version("vash")
except importlib.metadata.PackageNotFoundError:
    __version__ = "3.0.0"
