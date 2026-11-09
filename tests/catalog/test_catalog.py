"""Tests for the catalog (LAW 3 compliance)."""
import json
import pytest
from pathlib import Path
from vash.core.paths import vash_root
from vash.loader.manifest import _parse_frontmatter

def test_all_catalog_entries_have_licences():
    catalog = vash_root() / "catalog"
    if not catalog.exists():
        pytest.skip("No catalog")
    for path in catalog.rglob("*.md"):
        if path.name == "README.md" or path.name == "SKILL.md":
            continue
        meta = _parse_frontmatter(path)
        if meta and "id" in meta:
            assert "licence" in meta, f"{path} is missing a licence"

def test_all_stack_json_validate():
    import jsonschema
    catalog = vash_root() / "catalog" / "stacks"
    schema_path = vash_root() / "method" / "schemas" / "stack-pack.schema.json"
    if not catalog.exists() or not schema_path.exists():
        pytest.skip("No catalog or schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for path in catalog.rglob("stack.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)

def test_no_client_names_in_catalog():
    from vash.tools.gate1 import run
    catalog = vash_root() / "catalog"
    if not catalog.exists():
        pytest.skip("No catalog")
    report = run([catalog], vash_root(), ["G1-05"])
    assert report.ok
