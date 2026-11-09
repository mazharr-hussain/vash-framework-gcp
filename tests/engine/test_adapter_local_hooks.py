"""Tests for local hooks CI adapter."""
import pytest
from pathlib import Path
from vash.adapters.ci.local_hooks.adapter import Adapter
from vash.core.exceptions import NotAvailableYet

def test_start_run_empty():
    adapter = Adapter({"commands": []})
    ref = adapter.start_run("test", "main", {})
    assert ref.run_id.startswith("local-")
    res = adapter.get_run(ref.run_id)
    assert res.status == "completed"
    assert res.conclusion == "success"

def test_install_hooks_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("VASH_HOME", str(tmp_path))
    adapter = Adapter({})
    with pytest.raises(NotAvailableYet):
        adapter.install_hooks(tmp_path)

def test_install_hooks_success(monkeypatch, tmp_path):
    vash_home = tmp_path / "vash_home"
    hooks_dir = vash_home / "catalog" / "ci" / "local-hooks" / "hooks"
    hooks_dir.mkdir(parents=True)
    hook_file = hooks_dir / "pre-commit"
    hook_file.write_text("#!/bin/sh\nexit 0")

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git" / "hooks").mkdir(parents=True)

    monkeypatch.setenv("VASH_HOME", str(vash_home))
    adapter = Adapter({})
    written = adapter.install_hooks(repo)

    assert len(written) == 1
    assert written[0].name == "pre-commit"
    assert written[0].exists()
    assert written[0].stat().st_mode & 0o111
