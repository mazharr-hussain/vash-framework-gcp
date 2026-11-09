"""Tests for exceptions (C-02)."""
from vash.core.exceptions import (
    VashError, WriteNotAllowed, FreezeInvalid, AdapterNotInstalled,
)


def test_write_not_allowed_exit_code():
    e = WriteNotAllowed("Bad", "Fix")
    assert e.exit_code == 17
    assert str(e) == "Bad Fix: Fix"


def test_freeze_invalid_exit_code():
    e = FreezeInvalid("Bad", "Fix")
    assert e.exit_code == 11


def test_adapter_not_installed_exit_code():
    e = AdapterNotInstalled("Bad", "Fix")
    assert e.exit_code == 12


def test_base_exit_code():
    e = VashError("Bad", "Fix")
    assert e.exit_code == 1
