import json
from pathlib import Path

import pytest

from vash.cli.main import main
from vash.loader.load import generate_agents_md, load
from vash.loader.skills import find_agents, find_skills, split_frontmatter, validate_agent, validate_skill
from vash.tools.gate1 import run as gate1_run
from vash.tools.skill_suggest import suggest

skills_ref = pytest.importorskip("skills_ref")


def test_frontmatter_reads_nested_metadata():
    meta, body = split_frontmatter("---\nname: x\nmetadata:\n  vash-type: skill\n  vash-version: \"1.0\"\n---\n# Body\n")
    assert meta == {"name": "x", "metadata": {"vash-type": "skill", "vash-version": "1.0"}}
    assert body == "# Body\n"


def test_catalog_skills_pass_official_validator(tmp_repo):
    skills = find_skills(None)
    assert len(skills) >= 8
    for skill in skills.values():
        assert validate_skill(skill.path) == [], skill.name


def test_catalog_agents_are_valid(tmp_repo):
    for agent in find_agents(None).values():
        assert validate_agent(agent.path) == [], agent.name


def test_skill_new_creates_valid_project_skill(tmp_repo):
    assert main(["skill", "new", "apex-page-review", "--description",
                 "Review an APEXlang page against the project rules. Use for every page change.",
                 "--repo", str(tmp_repo)]) == 0
    skill_dir = tmp_repo / "skills" / "apex-page-review"
    assert validate_skill(skill_dir) == []
    meta, _ = split_frontmatter((skill_dir / "SKILL.md").read_text())
    assert meta["metadata"]["vash-source"] == "skills/apex-page-review"


def test_skill_new_refuses_bad_or_existing_names(tmp_repo, capsys):
    assert main(["skill", "new", "Bad_Name", "--description", "x", "--repo", str(tmp_repo)]) != 0
    assert main(["skill", "new", "code-reviewer", "--description", "x", "--repo", str(tmp_repo)]) != 0
    assert "already exists" in capsys.readouterr().out


def test_agent_new_creates_valid_agent(tmp_repo):
    assert main(["agent", "new", "apex-reviewer", "--description", "Reviews APEX changes.", "--repo", str(tmp_repo)]) == 0
    assert validate_agent(tmp_repo / "agents" / "apex-reviewer.md") == []


def test_load_installs_for_every_tool_and_keeps_hand_made(tmp_repo):
    main(["skill", "new", "release-patch", "--description", "Build a release patch. Use for every release.",
          "--repo", str(tmp_repo)])
    hand = tmp_repo / ".claude" / "skills" / "my-own"
    hand.mkdir(parents=True)
    (hand / "SKILL.md").write_text("---\nname: my-own\ndescription: mine\n---\n")
    load(tmp_repo)
    load(tmp_repo)  # second run removes only what the first wrote
    for folder in (".claude/skills", ".agents/skills"):
        assert (tmp_repo / folder / "release-patch" / "SKILL.md").exists()
    assert (hand / "SKILL.md").exists()
    agents_md = (tmp_repo / "AGENTS.md").read_text()
    assert "release-patch" in agents_md and agents_md.startswith("# AGENTS.md")


def test_agents_md_checked_by_gate1(tmp_repo):
    load(tmp_repo)
    assert gate1_run([tmp_repo / "AGENTS.md"], tmp_repo, ["G1-12"]).ok
    (tmp_repo / "AGENTS.md").write_text("# AGENTS.md\nedited by hand\n")
    assert not gate1_run([tmp_repo / "AGENTS.md"], tmp_repo, ["G1-12"]).ok


def test_gate1_g1_13_flags_bad_skill(tmp_repo):
    bad = tmp_repo / "skills" / "bad-skill"
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text("---\nname: other-name\ndescription: d\nowner: me\n---\n")
    report = gate1_run([bad / "SKILL.md"], tmp_repo, ["G1-13"])
    assert not report.ok
    assert any("must match" in f.message for f in report.findings)


def test_named_skills_go_into_the_prompt(tmp_repo):
    from tests.mocks.adapters.fake_llm import FakeLLM
    from vash.ava.runner import run_activity
    prompts = tmp_repo / "audit" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "t1_prompt.md").write_text("type: code\nskills: code-reviewer\nWrite code")
    coder = FakeLLM({}, ["x = 1"])
    run_activity("t1", tmp_repo, llm={"local": coder, "review": FakeLLM({}, ["Score: 95"])})
    assert '<skill name="code-reviewer">' in coder.requests[0]


def test_unknown_skill_in_prompt_is_refused(tmp_repo):
    from vash.ava.runner import run_activity
    from vash.core.exceptions import VashError
    prompts = tmp_repo / "audit" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "t2_prompt.md").write_text("type: code\nskills: no-such-skill\nWrite code")
    with pytest.raises(VashError, match="unknown skills"):
        run_activity("t2", tmp_repo, llm={})


def test_suggest_finds_repeated_work(tmp_repo):
    prompts = tmp_repo / "audit" / "prompts"
    prompts.mkdir(parents=True)
    for i, page in enumerate(["10", "20", "30"]):
        (prompts / f"p{i}_prompt.md").write_text(
            f"type: code\nfeature: KYC-{i}\nReview APEX page {page} against the page rules: "
            "privileges, redwood template, no HTML in PL/SQL, item help text.")
    (prompts / "other_prompt.md").write_text("type: artifact\nWrite the vision document for the platform.")
    found = suggest(tmp_repo)
    assert len(found) == 1
    assert found[0].tasks == ["p0", "p1", "p2"]
    assert main(["skill", "suggest", "--repo", str(tmp_repo)]) == 0


def test_manifest_lists_skills_and_agents(tmp_repo):
    from vash.loader.manifest import generate_manifest
    entries = generate_manifest(tmp_repo)["entries"]
    kinds = {(e["type"], e["id"]) for e in entries}
    assert ("skill", "code-reviewer") in kinds
    assert ("agent", "senior-validator") in kinds
