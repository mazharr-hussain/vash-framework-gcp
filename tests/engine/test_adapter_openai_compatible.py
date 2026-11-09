"""Tests for OpenAI-compatible LLM adapter."""
import json
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.llm.openai_compatible.adapter import Adapter
from vash.core.interfaces import RouteSettings
from vash.core.exceptions import RouteUnavailable, VashError

@patch("urllib.request.urlopen")
def test_reply(mock_urlopen, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"choices": [{"message": {"content": "Hi"}}], "usage": {"total_tokens": 10}}).encode()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    res = adapter.reply("Prompt", route)
    assert res.text == "Hi"

def test_missing_key():
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with patch.dict("os.environ", clear=True):
        with pytest.raises(RouteUnavailable, match="API key missing"):
            adapter.reply("Prompt", route)

def test_missing_settings():
    adapter = Adapter({})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url=None, key_env=None, timeout_s=10)
    with pytest.raises(VashError, match="base_url is required"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_http_error(mock_urlopen, monkeypatch):
    import urllib.error
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with pytest.raises(RouteUnavailable, match="API error 401"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_timeout(mock_urlopen, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_urlopen.side_effect = TimeoutError("timed out")
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with pytest.raises(RouteUnavailable, match="Connection failed"):
        adapter.reply("Prompt", route)
