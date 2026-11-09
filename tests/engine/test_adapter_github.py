"""Tests for GitHub forge adapter."""
import json
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.forge.github.adapter import Adapter
from vash.core.exceptions import RouteUnavailable, VashError

@patch("urllib.request.urlopen")
def test_create_issue(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "number": 1, "title": "T", "html_url": "http://test", "state": "open", "labels": []
    }).encode()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = Adapter({"repo": "owner/repo"})
    res = adapter.create_issue("T", "B", [])
    assert res.number == 1

def test_missing_token():
    adapter = Adapter({"repo": "owner/repo"})
    with patch.dict("os.environ", clear=True):
        with pytest.raises(RouteUnavailable, match="GITHUB_TOKEN"):
            adapter.create_issue("T", "B", [])

def test_missing_settings():
    with pytest.raises(VashError, match="Invalid or missing repo"):
        Adapter({})

@patch("urllib.request.urlopen")
def test_http_error(mock_urlopen, monkeypatch):
    import urllib.error
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)
    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(VashError, match="GitHub API error 401"):
        adapter.create_issue("T", "B", [])

@patch("urllib.request.urlopen")
def test_timeout(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_urlopen.side_effect = TimeoutError("timed out")
    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(RouteUnavailable, match="GitHub connection failed"):
        adapter.create_issue("T", "B", [])

def test_paginate_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    adapter = Adapter({"repo": "owner/repo"})
    with pytest.raises(RouteUnavailable, match="GITHUB_TOKEN"):
        adapter.list_issues()

@patch("urllib.request.urlopen")
def test_paginate_two_pages(mock_urlopen, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = json.dumps([{"number": 1, "title": "I1", "html_url": "", "state": "open", "labels": []}]).encode()
    mock_resp1.status = 200
    mock_resp1.headers = {"Link": '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next"'}

    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = json.dumps([{"number": 2, "title": "I2", "html_url": "", "state": "open", "labels": []}]).encode()
    mock_resp2.status = 200
    mock_resp2.headers = {}

    mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2]

    adapter = Adapter({"repo": "owner/repo"})
    res = adapter.list_issues()
    assert len(res) == 2
    assert res[0].number == 1
    assert res[1].number == 2
