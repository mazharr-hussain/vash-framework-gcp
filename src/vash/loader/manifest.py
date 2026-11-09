"""Generates ai-manifest.json from catalog entries."""
import json
import warnings
from pathlib import Path
from typing import Any
import jsonschema
from vash.core.paths import vash_root

ENTRY_FIELDS = ("id", "type", "source", "fork", "licence", "use", "version", "commit", "stacks", "adr", "search_log", "status")
def _parse_frontmatter(path: Path) -> dict[str, Any] | None:
    from vash.loader.skills import split_frontmatter
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    return meta


def _standard_entry(meta: dict[str, Any], kind: str) -> dict[str, Any] | None:
    """Map a standard-format skill or agent (name, license, metadata.vash-*) to a manifest entry."""
    md = meta.get("metadata")
    if not isinstance(md, dict) or "name" not in meta:
        return None
    entry = {
        "id": meta["name"],
        "type": md.get("vash-type", kind),
        "source": md.get("vash-source", ""),
        "licence": meta.get("license", md.get("vash-licence", "")),
        "use": md.get("vash-use", "fork"),
        "version": md.get("vash-version", ""),
        "commit": md.get("vash-commit", ""),
        "status": md.get("vash-status", "candidate"),
    }
    for key, field in (("vash-fork", "fork"), ("vash-search-log", "search_log"), ("vash-adr", "adr")):
        if md.get(key):
            entry[field] = md[key]
    return entry


def generate_manifest(repo_root: Path) -> dict[str, Any]:
    """Scan the catalog and build the manifest."""
    catalog = vash_root() / "catalog"
    entries = []

    licences: list[str] = []
    lic_path = catalog / "licences.json"
    if lic_path.exists():
        try:
            lic_data = json.loads(lic_path.read_text(encoding="utf-8"))
            licences = lic_data.get("licences_allowed", [])
        except Exception:
            pass

    schema_path = vash_root() / "method" / "schemas" / "ai-manifest.schema.json"
    validator = None
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

    if catalog.exists():
        for path in sorted(catalog.rglob("*.md")):
            if path.name == "README.md":
                continue
            meta = _parse_frontmatter(path)
            if not meta:
                continue
            if path.name == "SKILL.md" or path.parent.name == "agents":
                meta = _standard_entry(meta, "skill" if path.name == "SKILL.md" else "agent")
                if meta is None:
                    warnings.warn(f"Skipping {path}: no metadata block")
                    continue
            elif "id" in meta:
                meta = {k: v for k, v in meta.items() if k in ENTRY_FIELDS}
            else:
                continue
            if validator:
                try:
                    draft = {
                        "schema_version": "1.0",
                        "licences_allowed": licences,
                        "entries": [meta]
                    }
                    validator.validate(draft)
                except jsonschema.ValidationError as e:
                    warnings.warn(f"Skipping invalid manifest entry {path}: {e.message}")
                    continue
            entries.append(meta)

    return {
        "schema_version": "1.0",
        "licences_allowed": licences,
        "entries": entries
    }
