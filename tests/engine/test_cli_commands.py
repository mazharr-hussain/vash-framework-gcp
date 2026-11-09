"""Tests for CLI commands."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from vash.cli.load import run as load_run
from vash.cli.check import run as check_run
from vash.cli.status import run as status_run

def test_load_command(tmp_repo, capsys):
    assert load_run(tmp_repo) == 0
    assert "CLAUDE.md" in capsys.readouterr().out

def test_check_command(tmp_repo, capsys):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["stack"]["pack"] = "no-such-pack"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    assert check_run(tmp_repo) == 1
    assert "Stack pack" in capsys.readouterr().out

def test_status_command(tmp_repo, capsys):
    assert status_run(tmp_repo) == 0
    assert "Project: T" in capsys.readouterr().out
