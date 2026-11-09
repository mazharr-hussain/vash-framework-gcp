"""Tests for Gate 1 rules. Fails are built dynamically."""
import json
import pytest
from pathlib import Path
from vash.tools.gate1 import run, main
from vash.core.paths import vash_root

@pytest.fixture
def fixture_root():
    return vash_root() / "tests" / "fixtures"

def test_g1_01(fixture_root, tmp_path):
    assert run([fixture_root / "g1-01" / "pass" / "good.txt"], fixture_root, ["G1-01"]).ok
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"This file has trailing spaces.   \n")
    report = run([bad], tmp_path, ["G1-01"])
    assert not report.ok
    assert report.findings[0].rule_id == "G1-01"

def test_g1_02(fixture_root, tmp_path):
    assert run([fixture_root / "g1-02" / "pass" / "good.json"], fixture_root, ["G1-02"]).ok
    bad = tmp_path / "bad.json"
    bad.write_text("{ invalid: }")
    report = run([bad], tmp_path, ["G1-02"])
    assert not report.ok

def test_g1_03(fixture_root, tmp_path):
    assert run([fixture_root / "g1-03" / "pass" / "good.json"], fixture_root, ["G1-03"]).ok
    bad = tmp_path / "project-stack.json"
    bad.write_text('{"schema_version": "1.0"}')
    report = run([bad], tmp_path, ["G1-03"])
    assert not report.ok

def test_g1_04(fixture_root, tmp_path):
    assert run([fixture_root / "g1-04" / "pass" / "safe_core.py"], fixture_root, ["G1-04"]).ok

    core_dir = tmp_path / "src" / "vash" / "core"
    core_dir.mkdir(parents=True)
    bad = core_dir / "bad.py"
    bad.write_text('"""Bad file."""\ndef x(): return "github"')

    (tmp_path / "src" / "vash" / "adapters" / "forge" / "github").mkdir(parents=True)
    (tmp_path / "src" / "vash" / "adapters" / "forge" / "github" / "__init__.py").write_text("")

    report = run([bad], tmp_path, ["G1-04"])
    assert not report.ok

def test_g1_05(fixture_root, tmp_path, monkeypatch):
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    bad = catalog / "file.md"
    bad.write_text("Client Acme Corp")

    monkeypatch.setenv("VASH_DENY_NAMES_FILE", str(tmp_path / "deny.txt"))
    (tmp_path / "deny.txt").write_text("Acme Corp\n")

    report = run([bad], tmp_path, ["G1-05"])
    assert not report.ok

def test_g1_06(fixture_root, tmp_path):
    assert run([fixture_root / "g1-06" / "pass" / "safe.py"], fixture_root, ["G1-06"]).ok
    bad = tmp_path / "secret.py"
    bad.write_text('TOKEN = "' + "ghp_" + "A" * 36 + '"\n')
    report = run([bad], tmp_path, ["G1-06"])
    assert not report.ok

def test_g1_07(fixture_root, tmp_path):
    bad = tmp_path / "placeholder.py"
    bad.write_text(f"# {'TO' + 'DO'}: fix this")
    report = run([bad], tmp_path, ["G1-07"])
    assert not report.ok

def test_g1_08(fixture_root, tmp_path):
    assert run([fixture_root / "g1-08" / "pass" / "ADR-001.md"], fixture_root, ["G1-08"]).ok
    bad = tmp_path / "decisions" / "ADR-001.md"
    bad.parent.mkdir()
    bad.write_text("# ADR-001\n\n## Status\n")
    report = run([bad], tmp_path, ["G1-08"])
    assert not report.ok

def test_g1_09(fixture_root, tmp_path):
    assert run([fixture_root / "g1-09" / "pass" / "link.md"], fixture_root, ["G1-09"]).ok
    bad = tmp_path / "link.md"
    bad.write_text("[Bad Link](missing.md)")
    report = run([bad], tmp_path, ["G1-09"])
    assert not report.ok

def test_g1_10(fixture_root, tmp_path):
    art = tmp_path / "audit" / "artifacts"
    art.mkdir(parents=True)
    bad = art / "a.md"
    bad.write_text("```python\nprint(1)\n```")
    report = run([bad], tmp_path, ["G1-10"])
    assert not report.ok

def test_g1_11(fixture_root, tmp_path):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    bad = wf / "ci.yml"
    bad.write_text("uses: actions/checkout@v3\n")
    report = run([bad], tmp_path, ["G1-11"])
    assert not report.ok

def test_gate1_main_json(fixture_root, capsys):
    bad = fixture_root / "g1-01" / "pass" / "good.txt"
    assert main([str(bad), "--json"]) == 0
    captured = capsys.readouterr()
    assert '"ok": true' in captured.out

def test_gate1_rules_filter(fixture_root):
    bad = fixture_root / "g1-01" / "pass" / "good.txt"
    report = run([bad], fixture_root, ["G1-02"])
    assert report.ok
    assert report.files_checked == 1

def test_gate1_recursion(fixture_root):
    report = run([fixture_root / "g1-01"], fixture_root, ["G1-01"])
    assert report.ok
    assert report.files_checked > 0

def test_g1_05_skipped(fixture_root, tmp_path, monkeypatch):
    monkeypatch.delenv("VASH_DENY_NAMES_FILE", raising=False)
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    f = catalog / "file.md"
    f.write_text("Some text")
    report = run([f], tmp_path, ["G1-05"])
    assert report.ok
    assert report.findings[0].severity == "skipped"

def test_g1_12_skipped(fixture_root, tmp_path, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "vash.loader.load", None)
    f = tmp_path / "CLAUDE.md"
    f.write_text("Some text")
    report = run([f], tmp_path, ["G1-12"])
    assert report.ok
    assert report.findings[0].severity == "skipped"

def test_g1_12_in_sync(fixture_root, tmp_repo):
    from vash.loader.load import load
    load(tmp_repo)
    f = tmp_repo / "CLAUDE.md"
    report = run([f], tmp_repo, ["G1-12"])
    assert report.ok

def test_g1_04_tools(fixture_root):
    tools_dir = vash_root() / "src" / "vash" / "tools"
    report = run([tools_dir], vash_root(), ["G1-04"])
    assert report.ok
