"""R15: find repeated work in the saved prompts and propose a skill for it.

Deterministic and offline: prompts are normalised (header lines, ids, numbers and
paths removed) and grouped by text similarity; a group of `min_count` or more
prompts is a skill proposal. No model is called.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

HEADER_KEYS = ("type", "feature", "iteration", "skills", "activity", "threshold", "output path")


@dataclass(frozen=True)
class Proposal:
    name: str
    tasks: list[str]
    similarity: float
    sample: str


def normalise(text: str) -> str:
    kept = []
    for line in text.splitlines():
        key = line.partition(":")[0].strip().strip("*").strip().lower()
        if key in HEADER_KEYS:
            continue
        kept.append(line)
    out = "\n".join(kept).lower()
    out = re.sub(r"[\w./-]+\.(md|py|sql|pks|pkb|json|yml|apx)\b", " ", out)
    out = re.sub(r"\b[a-z]+-\d+\b|\b\d+\b", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def _name(texts: list[str]) -> str:
    words: dict[str, int] = {}
    for t in texts:
        for w in set(re.findall(r"[a-z]{4,}", t)):
            words[w] = words.get(w, 0) + 1
    common = [w for w, n in sorted(words.items(), key=lambda kv: (-kv[1], kv[0])) if n == len(texts)]
    return "-".join(common[:3]) or "repeated-task"


def suggest(repo_root: Path, min_count: int = 3, threshold: float = 0.8) -> list[Proposal]:
    prompt_dir = repo_root / "audit" / "prompts"
    if not prompt_dir.is_dir():
        return []
    items = []
    for path in sorted(prompt_dir.glob("*_prompt.md")):
        items.append((path.name[: -len("_prompt.md")], normalise(path.read_text(encoding="utf-8"))))

    groups: list[list[tuple[str, str]]] = []
    for task, text in items:
        if not text:
            continue
        for group in groups:
            if SequenceMatcher(None, group[0][1], text).ratio() >= threshold:
                group.append((task, text))
                break
        else:
            groups.append([(task, text)])

    proposals = []
    for group in groups:
        if len(group) < min_count:
            continue
        base = group[0][1]
        sims = [SequenceMatcher(None, base, t).ratio() for _, t in group[1:]]
        proposals.append(Proposal(
            name=_name([t for _, t in group]),
            tasks=[task for task, _ in group],
            similarity=round(min(sims), 2) if sims else 1.0,
            sample=base[:300],
        ))
    return proposals


def issue_body(proposal: Proposal) -> str:
    tasks = "\n".join(f"- `{t}`" for t in proposal.tasks)
    return (
        "Type: Task\nPriority: P3\n\n"
        f"Rule R15: the same kind of task ran {len(proposal.tasks)} times "
        f"(text similarity at least {proposal.similarity}).\n\n"
        f"Tasks:\n{tasks}\n\n"
        f"Proposed skill: `{proposal.name}` (rename as needed).\n\n"
        "Next: run the LAW 3 search, then `vash skill new <name>` and point the next prompts at it with `skills: <name>`."
    )
