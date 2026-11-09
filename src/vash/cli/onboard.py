"""VASH onboard command: set up a cloud runner for VASH in one step."""
import importlib
from typing import Any

from vash.core.exceptions import NotAvailableYet


def run(args: Any) -> int:
    """Load the onboarding of the chosen cloud adapter and run it."""
    module_name = f"vash.adapters.cloud.{args.cloud.replace('-', '_')}.onboard"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise NotAvailableYet(f"No onboarding for cloud '{args.cloud}'", "Pick a cloud adapter that ships an onboard module")
    return module.run_cli(args)
