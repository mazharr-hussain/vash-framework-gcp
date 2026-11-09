"""Tests for OCI cloud adapter."""
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.cloud.oci.adapter import Adapter
from vash.core.exceptions import AdapterNotInstalled, FreezeInvalid

@patch("subprocess.run")
def test_plan(mock_run, tmp_path):
    env_dir = tmp_path / "environments" / "dev"
    env_dir.mkdir(parents=True)
    adapter = Adapter({"iac_dir": str(tmp_path)})

    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Plan: 1 to add, 2 to change, 3 to destroy."

    res = adapter.plan("dev")
    assert res.changes == 6

@patch("subprocess.run")
def test_plan_no_changes(mock_run, tmp_path):
    env_dir = tmp_path / "environments" / "dev"
    env_dir.mkdir(parents=True)
    adapter = Adapter({"iac_dir": str(tmp_path)})

    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "No changes. Your infrastructure matches the configuration."

    res = adapter.plan("dev")
    assert res.changes == 0

def test_apply_unapproved(tmp_path):
    adapter = Adapter({"iac_dir": str(tmp_path)})
    with pytest.raises(FreezeInvalid):
        adapter.apply("dev", approved=False)

@patch("subprocess.run")
def test_missing_terraform(mock_run, tmp_path):
    env_dir = tmp_path / "environments" / "dev"
    env_dir.mkdir(parents=True)
    mock_run.side_effect = FileNotFoundError()
    adapter = Adapter({"iac_dir": str(tmp_path)})
    with pytest.raises(AdapterNotInstalled):
        adapter.plan("dev")
