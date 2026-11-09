"""Tests for the loader (C-13)."""
import json
import pytest
from pathlib import Path
from vash.loader.load import load, generate_claude_md
from vash.loader.manifest import generate_manifest

def test_generate_claude_md(tmp_repo):
    res = generate_claude_md(tmp_repo)
    assert "# CLAUDE.md" in res
    assert "Project Stack" in res

def test_load(tmp_repo):
    report = load(tmp_repo)
    assert (tmp_repo / "CLAUDE.md").exists()
    assert (tmp_repo / "ai-manifest.json").exists()
    assert len(report.written) > 0

def test_generate_manifest(tmp_repo):
    res = generate_manifest(tmp_repo)
    assert "schema_version" in res
    assert res["schema_version"] == "1.0"
