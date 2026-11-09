"""Shared pytest fixtures (C-17)."""
import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("VASH_HOME", str(checkout))
    repo = tmp_path / "repo"
    repo.mkdir()
    freeze = {
        "schema_version": "1.0",
        "project": {"id": "t", "name": "T", "repository": "t/t", "visibility": "private"},
        "vash": {"version": "3.0.0", "commit": "to-verify"},
        "stack": {"pack": "design-only", "pack_version": "1.0.0", "platform_version": {}},
        "forge": {"choice": "github", "settings": {"repo": "t/t"}},
        "ci": {"choice": "github-actions", "settings": {"repo": "t/t"}},
        "cloud": {"choice": "none", "settings": {}},
        "agents": [], "skills": [], "tools": [],
        "paths": {"allowed_write": ["src/**", "database/**"]},
        "models": {
            "routes": {
                "local": {"adapter": "ollama", "model": "to-verify", "vendor": "local", "timeout_s": 60},
                "review": {"adapter": "ollama", "model": "to-verify", "vendor": "local-b", "timeout_s": 60},
            },
            "intake": "local", "coder": "local", "critic": "review", "fallback": "local",
        },
        "thresholds": {"code": 90, "artifact": 88},
        "floor": 88,
    }
    (repo / "project-stack.json").write_text(json.dumps(freeze), encoding="utf-8")
    return repo
