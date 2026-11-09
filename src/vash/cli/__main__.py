"""Entry point for python -m vash.cli."""
import sys
from vash.cli.main import cli

if __name__ == "__main__":
    sys.exit(cli())
