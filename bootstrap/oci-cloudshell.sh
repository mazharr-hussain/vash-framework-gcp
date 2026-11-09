#!/bin/bash
# VASH onboarding for OCI Cloud Shell.
#   curl -fsSL https://raw.githubusercontent.com/mazharr-hussain/vash-framework/main/bootstrap/oci-cloudshell.sh | bash -s -- [options]
# Options are passed to `vash onboard oci` (for example --runner-repo owner/name, --down, --yes).
set -euo pipefail
SOURCE="${VASH_SOURCE:-git+https://github.com/mazharr-hussain/vash-framework.git}"

python_ok() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
}

PY=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null && python_ok "$candidate"; then
    PY="$candidate"
    break
  fi
done

VENV="$HOME/.vash/venv"
if [ -n "$PY" ]; then
  [ -x "$VENV/bin/vash" ] || "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  # --force-reinstall: the version number stays 3.0.0 between fixes, so a plain upgrade would keep old code.
  "$VENV/bin/pip" install -q --upgrade --force-reinstall "$SOURCE"
else
  # No Python 3.11+ here: uv fetches a standalone Python into the home folder (no root needed).
  if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  [ -x "$VENV/bin/vash" ] || uv venv --python 3.12 "$VENV"
  uv pip install -q --python "$VENV/bin/python" --reinstall-package vash "$SOURCE"
fi

# Run with the terminal as stdin, so the confirmations work under `curl | bash`.
if [ -t 0 ]; then
  exec "$VENV/bin/vash" onboard oci "$@"
else
  exec "$VENV/bin/vash" onboard oci "$@" </dev/tty
fi
