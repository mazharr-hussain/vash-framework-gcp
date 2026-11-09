"""Tests for the CLI main entry point."""
import pytest
from unittest.mock import patch
from vash.cli.main import main
from vash.core.exceptions import VashError

def test_version(capsys):
    assert main(["--version"]) == 0
    assert "vash" in capsys.readouterr().out

def test_no_command(capsys):
    assert main([]) == 2

def test_unknown_command():
    with pytest.raises(SystemExit):
        main(["unknown"])

@patch("vash.cli.init.run")
def test_init_command(mock_run):
    mock_run.return_value = 0
    assert main(["init"]) == 0
    mock_run.assert_called_once()

@patch("vash.cli.cost.run")
def test_cost_command(mock_run, capsys):
    from vash.core.exceptions import NotAvailableYet
    mock_run.side_effect = NotAvailableYet("cost meter", "Wave 2")
    assert main(["cost"]) == 0
    assert "cost meter" in capsys.readouterr().out
