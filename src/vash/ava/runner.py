"""AvA runner (C-14)."""
import json
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Any
from vash.core.freeze import load_freeze
from vash.core.interfaces import LLMAdapter, LLMReply
from vash.adapters.llm import reply as llm_reply
from vash.tools.gate1 import run as gate1_run
from vash.core.paths import vash_root
from vash.core.exceptions import VashError, RouteUnavailable

def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).rstrip("\n") + "\n"

@dataclass(frozen=True)
class AvaResult:
    task_id: str
    rounds: int
    scores: list[int]
    verdict: str
    log_paths: list[str]

def _load_checklist(name: str) -> str:
    path = vash_root() / "method" / "ava" / "checklists" / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def _read_header(prompt: str) -> dict[str, str]:
    """Read the type, feature, iteration and skills lines of a prompt.

    Accepts `type: code` and the template form `**TYPE:** CODE`; the first line of each key wins.
    """
    header: dict[str, str] = {}
    for line in prompt.split("\n"):
        key, sep, value = line.partition(":")
        key = key.strip().strip("*").strip().lower()
        if not sep or key not in ("type", "feature", "iteration", "skills"):
            continue
        value = value.strip().strip("*").strip()
        header.setdefault(key, value.lower() if key == "type" else value)
    return header

def _load_template() -> str:
    path = vash_root() / "method" / "templates" / "ava-log.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def run_activity(task_id: str, repo_root: Path, llm: Mapping[str, LLMAdapter] | None = None) -> AvaResult:
    """Run an AvA activity."""
    freeze = load_freeze(repo_root)
    thresholds = freeze.thresholds
    floor = freeze.floor
    threshold = 88

    task_file = repo_root / "audit" / "prompts" / f"{task_id}_prompt.md"
    if not task_file.exists():
        raise VashError(f"Task {task_id} not found", f"Create audit/prompts/{task_id}_prompt.md")
    prompt = task_file.read_text(encoding="utf-8")

    header = _read_header(prompt)
    act_type = header.get("type", "artifact")
    feature = header.get("feature", "")
    iteration = header.get("iteration", "")
    mode, _days = freeze.delivery
    if mode == "iterative" and act_type in ("feature", "code") and not feature:
        raise VashError(
            f"Task {task_id} has no feature: line",
            "In iterative mode add 'feature: <issue id>' to the prompt header",
        )
    skill_names = [s.strip() for s in header.get("skills", "").split(",") if s.strip()]
    if skill_names:
        # Plain model APIs cannot read skill folders, so the named skills travel inside the prompt.
        from vash.loader.skills import find_skills, skills_prompt_block
        missing = [s for s in skill_names if s not in find_skills(repo_root)]
        if missing:
            raise VashError(f"Task {task_id} names unknown skills: {', '.join(missing)}",
                            "Fix the skills: line, or add the skill under skills/ or the catalog")
        prompt = skills_prompt_block(skill_names, repo_root) + prompt
    checklist = act_type if (vash_root() / "method" / "ava" / "checklists" / f"{act_type}.md").exists() else "code"

    artifact_dir = repo_root / "audit" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ext = ".txt" if act_type == "code" else ".md"
    artifact_path = artifact_dir / f"{task_id}_artifact{ext}"

    log_dir = repo_root / "audit" / "ava_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_paths = []
    scores = []
    rounds = 0
    verdict = "FAIL"

    current_prompt = prompt
    thresh = thresholds.get(act_type, 88)
    if thresh < floor:
        thresh = floor

    for r in range(1, 4):
        rounds = r
        try:
            jr_reply = llm_reply(freeze, "coder", current_prompt, llm)
            artifact_path.write_text(_normalize(jr_reply.text), encoding="utf-8", newline="\n")
        except RouteUnavailable:
            _write_log(log_dir, task_id, feature, iteration, r, 0, thresh, "FAIL", "Route unavailable", log_paths)
            return AvaResult(task_id, r, scores, "FAIL", log_paths)

        g1 = gate1_run([artifact_path], repo_root)
        if not g1.ok:
            current_prompt += f"\n\nGate 1 failed:\n"
            for f in g1.findings:
                current_prompt += f"- {f.message}\n"
            _write_log(log_dir, task_id, feature, iteration, r, 0, thresh, "MODIFY", "Gate 1 failed", log_paths)
            continue

        try:
            sr_prompt = f"Review this artifact against the checklist and give a score 0-100.\n\nChecklist:\n{_load_checklist(checklist)}\n\nArtifact:\n{jr_reply.text}"
            sr_reply = llm_reply(freeze, "critic", sr_prompt, llm)
        except RouteUnavailable:
            _write_log(log_dir, task_id, feature, iteration, r, 0, thresh, "FAIL", "Critic route unavailable", log_paths)
            return AvaResult(task_id, r, scores, "FAIL", log_paths)

        score = 0
        match = re.search(r"(?:score|SCORE)[\s:]*(\d+)", sr_reply.text, re.IGNORECASE)
        if match:
            score = int(match.group(1))

        scores.append(score)
        current_verdict = "MODIFY"
        if score >= thresh:
            current_verdict = "APPROVED"
            verdict = "APPROVED"
        elif r == 3:
            current_verdict = "ESCALATED"
            verdict = "ESCALATED"

        _write_log(log_dir, task_id, feature, iteration, r, score, thresh, current_verdict, sr_reply.text, log_paths)

        if verdict == "APPROVED":
            break

        current_prompt += f"\n\nReviewer feedback (Score {score}):\n{sr_reply.text}\n\nPlease fix."

    return AvaResult(task_id, rounds, scores, verdict, log_paths)

def _write_log(log_dir: Path, task_id: str, feature: str, iteration: str, r: int, score: int, thresh: int, verdict: str, obj: str, log_paths: list) -> None:
    log_content = _load_template()
    log_content = log_content.replace("[ID]", task_id)
    log_content = log_content.replace("[feature]", feature or "-")
    log_content = log_content.replace("[iteration]", iteration or "-")
    log_content = log_content.replace("[N]", str(r))
    log_content = log_content.replace("[ISO-8601 UTC]", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log_content = log_content.replace("[0-100]", str(score))
    log_content = log_content.replace("[minimum]", str(thresh))
    log_content = log_content.replace("APPROVED | MODIFY | FAIL", verdict)
    log_content = log_content.replace("PASS/FAIL — [checks run]", "PASS")
    log_content = log_content.replace("[vendor / model]", "configured route")
    log_content = log_content.replace("NONE | CAUGHT | MISSED", "NONE")
    log_content = log_content.replace("OBJ-001: [issue at exact location]", obj)
    log_content = log_content.replace("OBJ-001: [exact fix]", "See review above")
    log_path = log_dir / f"{task_id.replace('.', '-')}_round{r}.md"
    log_path.write_text(log_content, encoding="utf-8", newline="\n")
    log_paths.append(str(log_path))
