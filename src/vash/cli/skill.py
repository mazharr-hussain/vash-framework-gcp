"""VASH skill and agent commands: create, validate and propose (rule R15)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from vash.core.exceptions import VashError
from vash.core.paths import vash_root
from vash.loader.skills import NAME_RE, find_agents, find_skills, validate_agent, validate_skill


def _check_name(name: str) -> None:
    if not NAME_RE.match(name) or len(name) > 64:
        raise VashError(f"Invalid name '{name}'", "Use lowercase letters, digits and single hyphens, at most 64 characters")


def _render(template: str, name: str, description: str, source: str, search: str) -> str:
    text = (vash_root() / "method" / "templates" / template).read_text(encoding="utf-8")
    title = name.replace("-", " ").capitalize()
    return (text.replace("@@NAME@@", name).replace("@@DESCRIPTION@@", description)
            .replace("@@SOURCE@@", source).replace("@@SEARCH@@", search).replace("@@TITLE@@", title))


def _base(args: Any, project_folder: str, catalog_folder: str) -> tuple[Path, str]:
    if args.catalog:
        root = vash_root()
        if not (root / ".git").exists():
            raise VashError("--catalog needs a VASH checkout", "Clone the VASH repository and set VASH_HOME to it")
        return root / "catalog" / catalog_folder, f"catalog/{catalog_folder}"
    return Path(args.repo) / project_folder, project_folder


def new_skill(args: Any) -> int:
    _check_name(args.name)
    if not args.description or len(args.description) > 1024:
        raise VashError("A description of 1-1024 characters is required", "Say what the skill does and when to use it")
    if args.name in find_skills(Path(args.repo)):
        raise VashError(f"Skill '{args.name}' already exists", "Reuse it (LAW 3), or pick another name")
    base, rel = _base(args, "skills", "skills")
    target = base / args.name
    target.mkdir(parents=True, exist_ok=False)
    (target / "SKILL.md").write_text(
        _render("skill.md", args.name, args.description, f"{rel}/{args.name}", args.searched),
        encoding="utf-8", newline="\n")
    print(f"Created {target / 'SKILL.md'}")
    print("Write the steps, then run `vash skill validate` and add it to the freeze or a prompt (`skills:`)")
    return 0


def new_agent(args: Any) -> int:
    _check_name(args.name)
    if not args.description or len(args.description) > 1024:
        raise VashError("A description of 1-1024 characters is required", "Say what the agent does and when to use it")
    if args.name in find_agents(Path(args.repo)):
        raise VashError(f"Agent '{args.name}' already exists", "Reuse it (LAW 3), or pick another name")
    base, rel = _base(args, "agents", "agents")
    base.mkdir(parents=True, exist_ok=True)
    target = base / f"{args.name}.md"
    target.write_text(
        _render("agent.md", args.name, args.description, f"{rel}/{args.name}.md", args.searched),
        encoding="utf-8", newline="\n")
    print(f"Created {target}")
    return 0


def validate(args: Any) -> int:
    repo = Path(args.repo)
    failed = 0
    skipped = False
    for name, skill in sorted(find_skills(repo).items()):
        errors = validate_skill(skill.path)
        if errors is None:
            skipped = True
            continue
        for e in errors:
            print(f"! skill {name} ({skill.origin}): {e}")
        failed += bool(errors)
    for name, agent in sorted(find_agents(repo).items()):
        errors = validate_agent(agent.path)
        for e in errors:
            print(f"! agent {name} ({agent.origin}): {e}")
        failed += bool(errors)
    if skipped:
        print("Skills not checked: install the official validator with pip install 'vash[skills]'")
    if failed:
        return 1
    print("All skills and agents valid." if not skipped else "All agents valid.")
    return 0


def suggest(args: Any) -> int:
    from vash.tools.skill_suggest import issue_body
    from vash.tools.skill_suggest import suggest as find

    proposals = find(Path(args.repo), min_count=args.min, threshold=args.similarity)
    if not proposals:
        print("No repeated work found.")
        return 0
    for p in proposals:
        print(f"- {p.name}: {len(p.tasks)} similar tasks ({', '.join(p.tasks)}), similarity >= {p.similarity}")
    if args.open_issues:
        from vash.core.freeze import load_freeze
        from vash.core.registry import load_adapter

        freeze = load_freeze(Path(args.repo))
        choice, settings = freeze.forge
        forge = load_adapter("forge", choice, settings)
        for p in proposals:
            ref = forge.create_issue(f"Skill proposal (R15): {p.name}", issue_body(p), args.label or [])
            print(f"Opened issue #{ref.number}: {ref.url}")
    return 0
