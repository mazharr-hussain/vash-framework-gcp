"""Proves no vendor is hard-coded by loading a real and a fake for each category."""
import sys
import types
import pytest
from vash.core.registry import load_adapter
from vash.core.interfaces import CATEGORY_INTERFACES, LLMAdapter
from tests.mocks.adapters.fake_forge import FakeForge
from tests.mocks.adapters.fake_ci import FakeCI
from tests.mocks.adapters.fake_cloud import FakeCloud
from tests.mocks.adapters.fake_llm import FakeLLM

def _register_fake(monkeypatch, category, name, cls):
    mod = types.ModuleType(f"vash.adapters.{category}.{name}")
    mod.Adapter = cls
    monkeypatch.setitem(sys.modules, f"vash.adapters.{category}.{name}", mod)

def test_forge_options(monkeypatch):
    _register_fake(monkeypatch, "forge", "fake", FakeForge)
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    real = load_adapter("forge", "github", {"repo": "o/r"})
    assert isinstance(real, CATEGORY_INTERFACES["forge"])
    fake = load_adapter("forge", "fake", {})
    assert isinstance(fake, CATEGORY_INTERFACES["forge"])

def test_ci_options(monkeypatch):
    _register_fake(monkeypatch, "ci", "fake", FakeCI)
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    real = load_adapter("ci", "github-actions", {"repo": "o/r"})
    assert isinstance(real, CATEGORY_INTERFACES["ci"])
    fake = load_adapter("ci", "fake", {})
    assert isinstance(fake, CATEGORY_INTERFACES["ci"])

def test_cloud_options(monkeypatch):
    _register_fake(monkeypatch, "cloud", "fake", FakeCloud)
    real = load_adapter("cloud", "oci", {})
    assert isinstance(real, CATEGORY_INTERFACES["cloud"])
    fake = load_adapter("cloud", "fake", {})
    assert isinstance(fake, CATEGORY_INTERFACES["cloud"])

def test_llm_options(monkeypatch):
    _register_fake(monkeypatch, "llm", "fake", FakeLLM)
    real = load_adapter("llm", "ollama", {})
    assert isinstance(real, CATEGORY_INTERFACES["llm"])
    fake = load_adapter("llm", "fake", {})
    assert isinstance(fake, CATEGORY_INTERFACES["llm"])
