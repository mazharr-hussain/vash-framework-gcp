"""Tests for write guard (C-10)."""
import os
import pytest
from pathlib import Path
from vash.mcp.write_guard import guarded_write, guarded_delete
from vash.core.exceptions import WriteNotAllowed


def test_write_allowed(tmp_repo):
    p = tmp_repo / "src" / "file.txt"
    result = guarded_write(p, "content", ["src/**"], tmp_repo)
    assert result.exists()
    assert result.read_text() == "content"


def test_write_traversal(tmp_repo):
    p = tmp_repo / "src" / ".." / ".." / "etc" / "passwd"
    with pytest.raises(WriteNotAllowed):
        guarded_write(p, "content", ["src/**"], tmp_repo)


def test_write_prefix_bypass(tmp_repo):
    p = tmp_repo / "src_evil" / "file.txt"
    with pytest.raises(WriteNotAllowed):
        guarded_write(p, "content", ["src/**"], tmp_repo)


def test_write_absolute_path(tmp_repo):
    p = Path("/etc/vash-test-passwd")
    with pytest.raises(WriteNotAllowed):
        guarded_write(p, "content", ["src/**"], tmp_repo)


def test_write_outside_repo(tmp_repo, tmp_path):
    p = tmp_path / "outside.txt"
    with pytest.raises(WriteNotAllowed):
        guarded_write(p, "content", ["src/**"], tmp_repo)


def test_write_symlink_escape(tmp_repo, tmp_path):
    outside = tmp_path / "outside_dir"
    outside.mkdir()
    link = tmp_repo / "src" / "link"
    link.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, link)
    target = link / "file.txt"
    with pytest.raises(WriteNotAllowed):
        guarded_write(target, "content", ["src/**"], tmp_repo)


def test_delete_allowed(tmp_repo):
    p = tmp_repo / "src" / "file.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("content")
    guarded_delete(p, ["src/**"], tmp_repo)
    assert not p.exists()


def test_delete_refused_outside(tmp_repo, tmp_path):
    p = tmp_path / "outside.txt"
    p.write_text("content")
    with pytest.raises(WriteNotAllowed):
        guarded_delete(p, ["src/**"], tmp_repo)


def test_delete_missing(tmp_repo):
    p = tmp_repo / "src" / "missing.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    with pytest.raises(WriteNotAllowed):
        guarded_delete(p, ["src/**"], tmp_repo)


def test_delete_directory(tmp_repo):
    p = tmp_repo / "src" / "dir"
    p.mkdir(parents=True, exist_ok=True)
    with pytest.raises(WriteNotAllowed):
        guarded_delete(p, ["src/**"], tmp_repo)
