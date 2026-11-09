"""Tests for freeze loading."""
import json
import pytest
from pathlib import Path
from vash.core.freeze import load_freeze
from vash.core.interfaces import RouteSettings
from vash.core.exceptions import FreezeFileMissing, FreezeInvalid


def test_load_freeze_valid(tmp_repo):
    freeze = load_freeze(tmp_repo)
    assert freeze.data["project"]["id"] == "t"
    assert freeze.floor == 88


def test_load_freeze_missing(tmp_path):
    with pytest.raises(FreezeFileMissing):
        load_freeze(tmp_path)


def test_load_freeze_invalid_json(tmp_repo):
    (tmp_repo / "project-stack.json").write_text("{bad json", encoding="utf-8")
    with pytest.raises(FreezeInvalid):
        load_freeze(tmp_repo)


def test_vendor_rule_refused(tmp_repo):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["models"]["routes"]["review"]["vendor"] = "local"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    with pytest.raises(FreezeInvalid, match="Critic vendor must differ"):
        load_freeze(tmp_repo)


def test_vendor_rule_od1_allowed(tmp_repo):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["models"]["routes"]["review"]["vendor"] = "local"
    data["owner_exception"] = "OD-1"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    freeze = load_freeze(tmp_repo)
    assert freeze.owner_exception == "OD-1"


def test_threshold_below_floor(tmp_repo):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["floor"] = 95
    data["thresholds"]["code"] = 90
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    with pytest.raises(FreezeInvalid, match="below floor 95"):
        load_freeze(tmp_repo)


def test_schema_error_path(tmp_repo):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["project"]["visibility"] = "not-a-valid-enum"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    with pytest.raises(FreezeInvalid, match="visibility"):
        load_freeze(tmp_repo)


def test_routes_returns_routesettings(tmp_repo):
    freeze = load_freeze(tmp_repo)
    assert isinstance(freeze.routes["local"], RouteSettings)
    assert freeze.routes["local"].vendor == "local"
    assert freeze.routes["review"].vendor == "local-b"


def test_schema_missing(tmp_repo, monkeypatch, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("VASH_HOME", str(empty))
    with pytest.raises(FreezeInvalid, match="Schema not found"):
        load_freeze(tmp_repo)


def test_undefined_route(tmp_repo):
    data = json.loads((tmp_repo / "project-stack.json").read_text())
    data["models"]["critic"] = "nope"
    (tmp_repo / "project-stack.json").write_text(json.dumps(data))
    with pytest.raises(FreezeInvalid, match="undefined route 'nope'"):
        load_freeze(tmp_repo)


def test_delivery_defaults_to_phased(tmp_repo):
    from vash.core.freeze import load_freeze
    assert load_freeze(tmp_repo).delivery == ("phased", None)


def test_delivery_iterative_is_valid(tmp_repo):
    import json
    from vash.core.freeze import load_freeze
    path = tmp_repo / "project-stack.json"
    data = json.loads(path.read_text())
    data["delivery"] = {"mode": "iterative", "iteration_days": 14}
    path.write_text(json.dumps(data))
    assert load_freeze(tmp_repo).delivery == ("iterative", 14)


def test_delivery_unknown_mode_is_refused(tmp_repo):
    import json
    import pytest
    from vash.core.exceptions import FreezeInvalid
    from vash.core.freeze import load_freeze
    path = tmp_repo / "project-stack.json"
    data = json.loads(path.read_text())
    data["delivery"] = {"mode": "waterfall-ish"}
    path.write_text(json.dumps(data))
    with pytest.raises(FreezeInvalid):
        load_freeze(tmp_repo)
