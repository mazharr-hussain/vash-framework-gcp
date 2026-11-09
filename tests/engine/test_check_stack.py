"""Tests for Stage 0 (check_stack)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from vash.tools.check_stack import run, main

def test_check_stack_pass(tmp_repo, monkeypatch, tmp_path):
    pack_dir = tmp_repo / "catalog" / "stacks" / "design-only"
    pack_dir.mkdir(parents=True)
    (pack_dir / "stack.json").write_text(json.dumps({
        "schema_version": "1.0", "id": "design-only", "name": "Design Only",
        "version": "1.0.0", "licence": "MIT", "description": "test",
        "platform": {}, "tools": [], "parts": {
            "skills": {"present": False, "reason": ""}, "rules": {"present": False, "reason": ""},
            "linters": {"present": False, "reason": ""}, "tests": {"present": False, "reason": ""},
            "deploy": {"present": False, "reason": ""}, "ui-tests": {"present": False, "reason": ""},
            "outputs": {"present": False, "reason": ""}
        }, "outputs": []
    }))

    dec_dir = tmp_repo / "decisions"
    dec_dir.mkdir()
    (dec_dir / "ADR-001.md").write_text("# ADR-001\n\n## Status\nACCEPTED\n")

    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["decisions"] = ["ADR-001"]
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))

    report = run(tmp_repo)
    assert report.ok is True, f"Problems: {report.problems}"

def test_check_stack_missing_adr(tmp_repo, monkeypatch):
    pack_dir = tmp_repo / "catalog" / "stacks" / "design-only"
    pack_dir.mkdir(parents=True)
    (pack_dir / "stack.json").write_text(json.dumps({
        "schema_version": "1.0", "id": "design-only", "name": "D", "version": "1.0.0", "licence": "MIT", "description": "t",
        "platform": {}, "tools": [], "parts": {k: {"present": False, "reason": ""} for k in ["skills", "rules", "linters", "tests", "deploy", "ui-tests", "outputs"]}, "outputs": []
    }))

    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["decisions"] = ["ADR-999"]
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))

    report = run(tmp_repo)
    assert report.ok is False
    assert any("ADR ADR-999 listed" in p for p in report.problems)

def test_check_stack_missing_freeze(tmp_path):
    report = run(tmp_path)
    assert not report.ok
    assert "Missing" in report.problems[0]

def test_check_stack_invalid_pack(tmp_repo, monkeypatch):
    pack_dir = tmp_repo / "catalog" / "stacks" / "design-only"
    pack_dir.mkdir(parents=True)
    (pack_dir / "stack.json").write_text("invalid json")
    report = run(tmp_repo)
    assert not report.ok
    assert "Stack pack" in report.problems[0]

def test_check_stack_tool_mismatch(tmp_repo, monkeypatch):
    pack_dir = tmp_repo / "catalog" / "stacks" / "design-only"
    pack_dir.mkdir(parents=True)
    (pack_dir / "stack.json").write_text(json.dumps({
        "schema_version": "1.0", "id": "design-only", "name": "D", "version": "1.0.0", "licence": "MIT", "description": "t",
        "platform": {}, "tools": [{"id": "fake", "version": "1.0", "version_command": ["echo", "2.0"]}],
        "parts": {k: {"present": False, "reason": ""} for k in ["skills", "rules", "linters", "tests", "deploy", "ui-tests", "outputs"]}, "outputs": []
    }))
    monkeypatch.setattr("subprocess.run", MagicMock(return_value=MagicMock(returncode=0, stdout="2.0\n")))
    report = run(tmp_repo)
    assert not report.ok
    assert "Tool fake expected 1.0, found 2.0" in report.problems[0]

def test_check_stack_adr_not_accepted(tmp_repo, monkeypatch):
    pack_dir = tmp_repo / "catalog" / "stacks" / "design-only"
    pack_dir.mkdir(parents=True)
    (pack_dir / "stack.json").write_text(json.dumps({
        "schema_version": "1.0", "id": "design-only", "name": "D", "version": "1.0.0", "licence": "MIT", "description": "t",
        "platform": {}, "tools": [], "parts": {k: {"present": False, "reason": ""} for k in ["skills", "rules", "linters", "tests", "deploy", "ui-tests", "outputs"]}, "outputs": []
    }))
    dec_dir = tmp_repo / "decisions"
    dec_dir.mkdir()
    (dec_dir / "ADR-001.md").write_text("# ADR-001\n\n## Status\nPROPOSED\n")
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["decisions"] = ["ADR-001"]
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    report = run(tmp_repo)
    assert not report.ok
    assert "ADR ADR-001 is not ACCEPTED" in report.problems[0]

def test_check_stack_main(tmp_repo, monkeypatch, capsys):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["stack"]["pack"] = "no-such-pack"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    monkeypatch.setattr("sys.argv", ["check_stack", "--repo", str(tmp_repo)])
    assert main(["--repo", str(tmp_repo)]) == 1
    captured = capsys.readouterr()
    assert "Problems found" in captured.out
