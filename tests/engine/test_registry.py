"""Tests for adapter registry."""
import sys
import types
import pytest
from vash.core.registry import load_adapter
from vash.core.interfaces import ForgeAdapter, IssueRef, PullRequestRef
from vash.core.exceptions import AdapterNotInstalled


def test_load_adapter_missing():
    with pytest.raises(AdapterNotInstalled):
        load_adapter("forge", "doesnotexist", {})


def test_load_adapter_unknown_category():
    with pytest.raises(AdapterNotInstalled):
        load_adapter("unknown", "whatever", {})


def test_load_adapter_fake_ok(monkeypatch):
    mod = types.ModuleType("vash.adapters.forge.fake_ok")

    class Adapter(ForgeAdapter):
        def create_issue(self, title, body, labels): return IssueRef(1, title, "", "", ())
        def list_issues(self, state="open", labels=()): return []
        def read_board(self, board): return []
        def open_pr(self, head, base, title, body): return PullRequestRef(1, "", head, base, "")
        def merge_pr(self, number, method="squash"): pass
        def export_status(self): return {}

    mod.Adapter = Adapter
    monkeypatch.setitem(sys.modules, "vash.adapters.forge.fake_ok", mod)
    result = load_adapter("forge", "fake-ok", {})
    assert isinstance(result, ForgeAdapter)


def test_load_adapter_import_error(monkeypatch):
    import importlib.abc
    import importlib.machinery

    class FailingLoader(importlib.abc.Loader):
        def create_module(self, spec):
            return None
        def exec_module(self, module):
            raise ImportError("cannot import name 'x' from 'y'")

    class FailingFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "vash.adapters.forge.broken":
                return importlib.machinery.ModuleSpec(
                    fullname, FailingLoader()
                )
            return None

    finder = FailingFinder()
    monkeypatch.setattr(sys, "meta_path", [finder] + sys.meta_path)
    with pytest.raises(AdapterNotInstalled, match="failed to import"):
        load_adapter("forge", "broken", {})
