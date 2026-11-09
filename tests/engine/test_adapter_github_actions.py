"""Tests for GitHub Actions CI adapter."""
import json
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.ci.github_actions.adapter import Adapter
from vash.core.exceptions import RouteUnavailable, VashError

@patch("urllib.request.urlopen")
def test_get_run(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "id": 123, "status": "completed", "conclusion": "success", "html_url": "http://test"
    }).encode()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = Adapter({"repo": "owner/repo"})
    res = adapter.get_run("123")
    assert res.status == "completed"

def test_missing_token():
    adapter = Adapter({"repo": "owner/repo"})
    with patch.dict("os.environ", clear=True):
        with pytest.raises(RouteUnavailable, match="GITHUB_TOKEN"):
            adapter.get_run("123")

def test_missing_settings():
    with pytest.raises(VashError, match="Invalid or missing repo"):
        Adapter({})

@patch("urllib.request.urlopen")
def test_http_error(mock_urlopen, monkeypatch):
    import urllib.error
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(VashError, match="GitHub Actions API error 404"):
        adapter.get_run("123")

@patch("urllib.request.urlopen")
def test_timeout(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_urlopen.side_effect = TimeoutError("timed out")
    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(RouteUnavailable, match="GitHub Actions connection failed"):
        adapter.get_run("123")

@patch("urllib.request.urlopen")
def test_start_run_success(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_dispatch = MagicMock()
    mock_dispatch.status = 204
    mock_dispatch.read.return_value = b""

    mock_runs = MagicMock()
    mock_runs.status = 200
    mock_runs.read.return_value = json.dumps({
        "workflow_runs": [{"id": 999, "html_url": "http://run"}]
    }).encode()

    mock_urlopen.return_value.__enter__.side_effect = [mock_dispatch, mock_runs]

    adapter = Adapter({"repo": "owner/repo"})
    res = adapter.start_run("test.yml", "main", {}, sleep_fn=lambda x: None)
    assert res.run_id == "999"
    assert res.url == "http://run"

@patch("urllib.request.urlopen")
def test_start_run_timeout(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_dispatch = MagicMock()
    mock_dispatch.status = 204
    mock_runs = MagicMock()
    mock_runs.status = 200
    mock_runs.read.return_value = json.dumps({"workflow_runs": []}).encode()

    mock_urlopen.return_value.__enter__.side_effect = [mock_dispatch] + [mock_runs] * 10

    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(VashError, match="Could not find the dispatched run"):
        adapter.start_run("test.yml", "main", {}, sleep_fn=lambda x: None)
