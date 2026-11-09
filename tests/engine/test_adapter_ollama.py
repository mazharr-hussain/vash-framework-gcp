"""Tests for Ollama LLM adapter."""
import json
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.llm.ollama.adapter import Adapter
from vash.core.interfaces import RouteSettings
from vash.core.exceptions import RouteUnavailable

@patch("urllib.request.urlopen")
def test_reply(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"response": "Hi", "prompt_eval_count": 10, "eval_count": 5}).encode()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = Adapter({})
    route = RouteSettings(name="test", adapter="ollama", model="llama", vendor="local", base_url=None, key_env=None, timeout_s=10)
    res = adapter.reply("Prompt", route)
    assert res.text == "Hi"
    assert res.usage["prompt_tokens"] == 10

@patch("urllib.request.urlopen")
def test_ollama_http_error(mock_urlopen):
    import urllib.error
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Server Error", {}, None)
    adapter = Adapter({})
    route = RouteSettings(name="test", adapter="ollama", model="llama", vendor="local", base_url=None, key_env=None, timeout_s=10)
    with pytest.raises(RouteUnavailable, match="Ollama error 500"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_ollama_timeout(mock_urlopen):
    mock_urlopen.side_effect = TimeoutError("timed out")
    adapter = Adapter({})
    route = RouteSettings(name="test", adapter="ollama", model="llama", vendor="local", base_url=None, key_env=None, timeout_s=10)
    with pytest.raises(RouteUnavailable, match="Ollama connection failed"):
        adapter.reply("Prompt", route)
