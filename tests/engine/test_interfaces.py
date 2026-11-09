"""Tests for interfaces (C-03)."""
from dataclasses import is_dataclass
import pytest

from vash.core.interfaces import (
    IssueRef, BoardItem, PullRequestRef, RunRef, RunResult,
    CloudPlan, VersionCheck, RouteSettings, LLMReply,
    ForgeAdapter, CIAdapter, CloudAdapter, LLMAdapter, StackPack,
    CATEGORY_INTERFACES,
)


def test_dataclasses_frozen():
    for cls in [IssueRef, BoardItem, PullRequestRef, RunRef, RunResult,
                CloudPlan, VersionCheck, RouteSettings, LLMReply]:
        assert is_dataclass(cls), cls
        assert cls.__dataclass_params__.frozen, cls


def test_abcs_not_instantiable():
    for cls in [ForgeAdapter, CIAdapter, CloudAdapter, LLMAdapter, StackPack]:
        with pytest.raises(TypeError):
            cls({})


def test_forge_subclass_instantiable():
    class FakeForge(ForgeAdapter):
        def create_issue(self, title, body, labels): return IssueRef(1, title, "", "", ())
        def list_issues(self, state="open", labels=()): return []
        def read_board(self, board): return []
        def open_pr(self, head, base, title, body): return PullRequestRef(1, "", head, base, "")
        def merge_pr(self, number, method="squash"): pass
        def export_status(self): return {}
    assert FakeForge({}) is not None


def test_category_interfaces_complete():
    for name in ("forge", "ci", "cloud", "llm"):
        assert name in CATEGORY_INTERFACES
