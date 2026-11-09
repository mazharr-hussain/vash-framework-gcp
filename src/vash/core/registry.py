"""Adapter registry (C-04)."""
import importlib
from typing import Mapping, Any
from vash.core.interfaces import CATEGORY_INTERFACES
from vash.core.exceptions import AdapterNotInstalled


def load_adapter(category: str, choice: str, settings: Mapping[str, Any]) -> object:
    pkg_name = choice.replace("-", "_")
    mod_path = f"vash.adapters.{category}.{pkg_name}"
    try:
        mod = importlib.import_module(mod_path)
    except ModuleNotFoundError as e:
        name = e.name or ""
        if name == mod_path or mod_path.startswith(name + "."):
            raise AdapterNotInstalled(
                f"Adapter {category}/{choice} not found",
                "Check catalog id in project-stack.json"
            ) from e
        raise AdapterNotInstalled(
            f"Adapter {mod_path} failed to import: {e}",
            "Install the adapter's dependencies"
        ) from e
    except ImportError as e:
        raise AdapterNotInstalled(
            f"Adapter {mod_path} failed to import: {e}",
            "Install the adapter's dependencies"
        ) from e
    AdapterClass = getattr(mod, "Adapter", None)
    if not AdapterClass:
        raise AdapterNotInstalled(
            f"No Adapter class in {mod_path}",
            "Export Adapter from adapter.py"
        )
    expected = CATEGORY_INTERFACES.get(category)
    if expected and not issubclass(AdapterClass, expected):
        raise AdapterNotInstalled(
            f"{mod_path} does not subclass {expected.__name__}",
            "Fix adapter inheritance"
        )
    return AdapterClass(settings)
