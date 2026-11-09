"""Tests for the AvA runner (C-14)."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from vash.ava.runner import run_activity
from tests.mocks.adapters.fake_llm import FakeLLM

def test_run_activity_approve(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("type: code\nWrite code")

    coder = FakeLLM({}, ["```python\nx = 1\n```"])
    critic = FakeLLM({}, ["Score: 95\nLooks good."])

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "APPROVED"
    assert res.scores == [95]

def test_run_activity_modify(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("Write code")

    coder = FakeLLM({}, ["bad code"] * 3)
    critic = FakeLLM({}, ["Score: 50\nFix this."] * 3)

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "ESCALATED"
    assert len(res.scores) == 3

def test_run_activity_gate1_fail(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("Write code")

    coder = FakeLLM({}, ['TOKEN = "' + "ghp_" + "A" * 36 + '"'] * 3)
    critic = FakeLLM({}, ["Score: 95"] * 3)

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "FAIL"
    assert res.scores == []
    assert len(res.log_paths) == 3

def test_run_activity_missing_prompt(tmp_repo):
    with pytest.raises(Exception):
        run_activity("missing", tmp_repo)


def _iterative(tmp_repo):
    path = tmp_repo / "project-stack.json"
    data = json.loads(path.read_text())
    data["delivery"] = {"mode": "iterative", "iteration_days": 14}
    path.write_text(json.dumps(data))


def test_feature_and_iteration_written_to_log(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "f1_prompt.md").write_text("**TYPE:** FEATURE\n**FEATURE:** KYC-12\niteration: S3\nDesign it")
    coder = FakeLLM({}, ["# Feature design\nRequirements listed."])
    critic = FakeLLM({}, ["Score: 92\nGood."])
    res = run_activity("f1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "APPROVED"
    log = Path(res.log_paths[0]).read_text()
    assert "**FEATURE:** KYC-12" in log
    assert "**ITERATION:** S3" in log


def test_feature_checklist_sent_to_critic(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "f2_prompt.md").write_text("type: feature\nfeature: KYC-13\nDesign it")
    critic = FakeLLM({}, ["Score: 90"])
    run_activity("f2", tmp_repo, llm={"local": FakeLLM({}, ["# Design\nText."]), "review": critic})
    assert "Checklist: Feature Activity" in critic.requests[0]


def test_iterative_mode_requires_feature_line(tmp_repo):
    from vash.core.exceptions import VashError
    _iterative(tmp_repo)
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "c1_prompt.md").write_text("type: code\nWrite code")
    with pytest.raises(VashError, match="no feature: line"):
        run_activity("c1", tmp_repo, llm={"local": FakeLLM({}, ["x"]), "review": FakeLLM({}, ["Score: 95"])})


def test_phased_mode_needs_no_feature_line(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "c2_prompt.md").write_text("type: code\nWrite code")
    res = run_activity("c2", tmp_repo, llm={"local": FakeLLM({}, ["x = 1"]), "review": FakeLLM({}, ["Score: 95"])})
    assert res.verdict == "APPROVED"
