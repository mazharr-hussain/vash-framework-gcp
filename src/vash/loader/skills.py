"""Portable skills and agents (Agent Skills open standard, agentskills.io).

A skill is a folder with SKILL.md: YAML frontmatter with `name` and `description`
(optional `license`, `compatibility`, `metadata`, `allowed-tools`), then Markdown.
VASH keeps its own fields under `metadata` with the `vash-` prefix, so every tool
that reads the standard accepts VASH skills unchanged.

An agent has no cross-tool standard yet. VASH keeps it as one neutral Markdown file
(frontmatter `name`, `description`, optional `skills`, `tools`, `metadata`) and the
loader renders it per tool.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vash.core.paths import vash_root

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
AGENT_FIELDS = {"name", "description", "skills", "tools", "metadata"}
PROJECT_SKILLS = "skills"
PROJECT_AGENTS = "agents"


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path
    meta: dict[str, Any]
    body: str
    origin: str  # "catalog" or "project"


@dataclass(frozen=True)
class Agent:
    name: str
    path: Path
    meta: dict[str, Any]
    body: str
    origin: str
    skills: list[str] = field(default_factory=list)


def _value(raw: str) -> Any:
    val = raw.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [x.strip().strip("\"'") for x in inner.split(",")] if inner else []
    return val


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Return (frontmatter, body). Supports flat keys, [a, b] lists and one nested map level."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    data: dict[str, Any] = {}
    current: str | None = None
    for line in text[4:end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and current is not None:
            key, sep, val = line.strip().partition(":")
            if sep:
                data[current][key.strip()] = _value(val)
            continue
        key, sep, val = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        if val.strip() == "":
            data[key] = {}
            current = key
        else:
            data[key] = _value(val)
            current = None
    return data, text[end + 5:]


def vash_meta(meta: dict[str, Any], key: str, default: str = "") -> str:
    md = meta.get("metadata")
    if isinstance(md, dict):
        return str(md.get(f"vash-{key}", default))
    return default


# ---- discovery ---------------------------------------------------------

def _skill_roots(repo_root: Path | None) -> list[tuple[Path, str]]:
    roots = [(vash_root() / "catalog" / "skills", "catalog")]
    if repo_root is not None:
        roots.append((repo_root / PROJECT_SKILLS, "project"))
    return roots


def _agent_roots(repo_root: Path | None) -> list[tuple[Path, str]]:
    roots = [(vash_root() / "catalog" / "agents", "catalog")]
    if repo_root is not None:
        roots.append((repo_root / PROJECT_AGENTS, "project"))
    return roots


def read_skill(skill_dir: Path, origin: str = "catalog") -> Skill:
    meta, body = split_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    meta = meta or {}
    return Skill(str(meta.get("name", skill_dir.name)), skill_dir, meta, body, origin)


def read_agent(path: Path, origin: str = "catalog") -> Agent:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    meta = meta or {}
    skills = meta.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    return Agent(str(meta.get("name", path.stem)), path, meta, body, origin, list(skills))


def find_skills(repo_root: Path | None = None) -> dict[str, Skill]:
    """All skills by name; a project skill overrides a catalog skill of the same name."""
    found: dict[str, Skill] = {}
    for root, origin in _skill_roots(repo_root):
        if root.is_dir():
            for d in sorted(p for p in root.iterdir() if (p / "SKILL.md").is_file()):
                skill = read_skill(d, origin)
                found[skill.name] = skill
    return found


def find_agents(repo_root: Path | None = None) -> dict[str, Agent]:
    found: dict[str, Agent] = {}
    for root, origin in _agent_roots(repo_root):
        if root.is_dir():
            for p in sorted(root.glob("*.md")):
                if p.name == "README.md":
                    continue
                agent = read_agent(p, origin)
                found[agent.name] = agent
    return found


# ---- validation --------------------------------------------------------

def validate_skill(skill_dir: Path) -> list[str] | None:
    """Errors from the official Agent Skills validator (skills-ref); None if it is not installed."""
    try:
        from skills_ref import validate
    except ImportError:
        return None
    return list(validate(skill_dir))


def validate_agent(path: Path) -> list[str]:
    """VASH's neutral agent format (no cross-tool standard exists yet)."""
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    if meta is None:
        return ["Agent file must start with YAML frontmatter (---)"]
    errors = []
    extra = set(meta) - AGENT_FIELDS
    if extra:
        errors.append(f"Unexpected fields in frontmatter: {', '.join(sorted(extra))}; put VASH fields under metadata")
    name = meta.get("name", "")
    if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"Agent name '{name}' must be lowercase letters, digits and single hyphens (max 64)")
    elif name != path.stem:
        errors.append(f"File name '{path.name}' must match agent name '{name}'")
    desc = meta.get("description", "")
    if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024:
        errors.append("Field 'description' must be 1-1024 characters")
    if "metadata" in meta and not isinstance(meta["metadata"], dict):
        errors.append("Field 'metadata' must be a map")
    return errors


# ---- rendering ---------------------------------------------------------

def render_claude_agent(agent: Agent) -> str:
    """The agent as a Claude Code subagent file."""
    lines = ["---", f"name: {agent.name}", f"description: {agent.meta.get('description', '')}"]
    tools = agent.meta.get("tools")
    if tools:
        lines.append(f"tools: {', '.join(tools) if isinstance(tools, list) else tools}")
    lines.append("---")
    body = agent.body.lstrip("\n")
    if agent.skills:
        body += "\n## Skills\n" + "".join(f"- {s}\n" for s in agent.skills)
    return "\n".join(lines) + "\n\n" + body


def skills_prompt_block(names: list[str], repo_root: Path | None) -> str:
    """Full text of the named skills, for models that cannot read skill folders."""
    available = find_skills(repo_root)
    parts = []
    for name in names:
        skill = available.get(name)
        if skill is None:
            continue
        parts.append(f"<skill name=\"{skill.name}\">\n{skill.body.strip()}\n</skill>")
    if not parts:
        return ""
    return "Use these skills for the task:\n\n" + "\n\n".join(parts) + "\n\n"
