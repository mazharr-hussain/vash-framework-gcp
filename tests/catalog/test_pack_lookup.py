"""The stack pack is found in VASH's catalog when the project has none."""
from vash.core.freeze import load_stack_pack


def test_pack_from_vash_catalog(tmp_repo):
    data = load_stack_pack(tmp_repo, "design-only")
    assert data["id"] == "design-only"
