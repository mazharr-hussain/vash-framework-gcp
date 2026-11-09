"""Extra Gate 1 rules for GitHub Actions."""
import re
from pathlib import Path
from vash.tools.gate1 import Rule, Finding

def _check_action_pins(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    if ".github/workflows/" not in str(path).replace("\\", "/"):
        return findings
    if path.suffix not in (".yml", ".yaml"):
        return findings
    for i, line in enumerate(text.split("\n"), 1):
        match = re.search(r"uses:\s*([^\s#]+)", line)
        if match:
            action = match.group(1)
            if action.startswith("./"):
                continue
            if "@" in action:
                _, sha = action.split("@", 1)
                if not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
                    findings.append(Finding("G1-11", str(path), i, f"Action {action} not pinned to a 40-char SHA", "Pin to a 40-character SHA"))
            else:
                findings.append(Finding("G1-11", str(path), i, f"Action {action} not pinned", "Pin to a 40-character SHA"))
    return findings

RULES = [
    Rule("G1-11", "Action pins", ("*.yml", "*.yaml"), _check_action_pins, "Pin to a 40-character SHA")
]
