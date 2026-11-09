"""Tests for the LLM interface."""
import pytest
from unittest.mock import MagicMock
from vash.adapters.llm import reply, route_for
from vash.core.exceptions import RouteUnavailable
from tests.mocks.adapters.fake_llm import FakeLLM
from vash.core.interfaces import RouteSettings

def test_route_for():
    freeze = MagicMock()
    freeze.data = {"models": {"intake": "local"}}
    freeze.routes = {"local": RouteSettings(name="local", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)}
    r = route_for(freeze, "intake")
    assert r.name == "local"

def test_reply_intake_no_fallback():
    freeze = MagicMock()
    freeze.data = {"models": {"intake": "local", "fallback": "fall"}}
    r1 = RouteSettings(name="local", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)
    r2 = RouteSettings(name="fall", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)
    freeze.routes = {"local": r1, "fall": r2}

    adapter = FakeLLM({}, [])
    with pytest.raises(RouteUnavailable):
        reply(freeze, "intake", "prompt", adapters={"local": adapter, "fall": adapter})

def test_reply_coder_fallback():
    freeze = MagicMock()
    freeze.data = {"models": {"coder": "coder", "fallback": "fall"}}
    r1 = RouteSettings(name="coder", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)
    r2 = RouteSettings(name="fall", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)
    freeze.routes = {"coder": r1, "fall": r2}

    coder_adapter = FakeLLM({}, [])
    fall_adapter = FakeLLM({}, ["Fallback text"])
    res = reply(freeze, "coder", "prompt", adapters={"coder": coder_adapter, "fall": fall_adapter})
    assert res.text == "Fallback text"
    assert res.degraded is True

def test_reply_coder_no_fallback():
    freeze = MagicMock()
    freeze.data = {"models": {"coder": "coder"}}
    r1 = RouteSettings(name="coder", adapter="ollama", model="m", vendor="v", base_url=None, key_env=None, timeout_s=10)
    freeze.routes = {"coder": r1}

    coder_adapter = FakeLLM({}, [])
    with pytest.raises(RouteUnavailable):
        reply(freeze, "coder", "prompt", adapters={"coder": coder_adapter})
