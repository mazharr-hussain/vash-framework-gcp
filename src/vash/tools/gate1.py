"""Gate 1 deterministic checks (C-11)."""
import sys
import json
import re
import argparse
import tomllib
import pkgutil
import importlib
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Callable, Any
import subprocess
from vash.core.exceptions import VashError
from vash.core.paths import vash_root

@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int | None
    message: str
    fix: str
    severity: str = "error"

@dataclass(frozen=True)
class Gate1Report:
    findings: list[Finding]
    files_checked: int
    ok: bool

@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    applies_to: tuple[str, ...]
    check: Callable[[Path, str, Path], list[Finding]]
    fix: str

def _check_format(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    if "\r\n" in text:
        findings.append(Finding("G1-01", str(path), None, "CRLF detected", "Use LF line endings"))
    if text.startswith("\ufeff"):
        findings.append(Finding("G1-01", str(path), None, "BOM detected", "Remove BOM"))
    if not text.endswith("\n"):
        findings.append(Finding("G1-01", str(path), None, "Missing final newline", "Add a newline"))
    if text.endswith("\n\n"):
        findings.append(Finding("G1-01", str(path), None, "Multiple final newlines", "Use exactly one newline"))
    for i, line in enumerate(text.split("\n"), 1):
        if line.rstrip() != line:
            findings.append(Finding("G1-01", str(path), i, "Trailing spaces", "Remove trailing spaces"))
            break
    return findings

def _check_syntax(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    if path.suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            findings.append(Finding("G1-02", str(path), e.lineno, f"Invalid JSON: {e.msg}", "Fix JSON syntax"))
    elif path.suffix == ".toml":
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            findings.append(Finding("G1-02", str(path), None, f"Invalid TOML: {e}", "Fix TOML syntax"))
    elif path.suffix == ".py":
        try:
            compile(text, str(path), "exec")
        except SyntaxError as e:
            findings.append(Finding("G1-02", str(path), e.lineno, f"Syntax error: {e.msg}", "Fix Python syntax"))
    return findings

def _check_schemas(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    schema_dir = vash_root() / "method" / "schemas"
    if path.name == "project-stack.json":
        findings.extend(_validate_schema(path, text, schema_dir / "project-stack.schema.json"))
    elif path.name == "ai-manifest.json":
        findings.extend(_validate_schema(path, text, schema_dir / "ai-manifest.schema.json"))
    elif path.name == "stack.json":
        findings.extend(_validate_schema(path, text, schema_dir / "stack-pack.schema.json"))
    return findings

def _validate_schema(path: Path, text: str, schema_path: Path) -> list[Finding]:
    if not schema_path.exists():
        return []
    try:
        import jsonschema
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        data = json.loads(text)
        jsonschema.Draft202012Validator(schema).validate(data)
    except Exception as e:
        return [Finding("G1-03", str(path), None, f"Schema validation failed: {e}", "Fix the schema fields")]
    return []

def _check_vendor_names(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return []
    p_str = str(rel).replace("\\", "/")
    vendor_free_dirs = ["src/vash/core/", "src/vash/tools/", "src/vash/cli/", "src/vash/loader/", "src/vash/ava/", "src/vash/mcp/"]
    if not any(p_str.startswith(v) for v in vendor_free_dirs):
        return []

    forbidden = set()
    adapters_dir = repo_root / "src" / "vash" / "adapters"
    if adapters_dir.exists():
        for cat_dir in adapters_dir.iterdir():
            if cat_dir.is_dir():
                for choice in cat_dir.iterdir():
                    if choice.is_dir() and not choice.name.startswith("_") and (choice / "__init__.py").exists():
                        forbidden.add(choice.name.lower())
                        forbidden.add(choice.name.replace("_", "-").lower())
                        forbidden.add(choice.name.replace("-", "_").lower())

    catalog_dir = repo_root / "catalog"
    if catalog_dir.exists():
        for cat_dir in catalog_dir.iterdir():
            if cat_dir.is_dir():
                for entry in cat_dir.iterdir():
                    if entry.is_file() and entry.suffix == ".md" and entry.stem.lower() != "readme":
                        forbidden.add(entry.stem.lower())

    for i, line in enumerate(text.split("\n"), 1):
        for v in forbidden:
            if v and re.search(rf"\b{re.escape(v)}\b", line, re.IGNORECASE):
                findings.append(Finding("G1-04", str(path), i, f"Forbidden vendor name '{v}' in vendor-free folder", "Move vendor logic to an adapter"))
    return findings

def _check_deny_names(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return []
    if not str(rel).replace("\\", "/").startswith("catalog/"):
        return findings

    import os
    deny_file = os.environ.get("VASH_DENY_NAMES_FILE")
    if not deny_file:
        return [Finding("G1-05", str(path), None, "skipped: no deny list", "Set VASH_DENY_NAMES_FILE to a file with client names", "skipped")]
    deny_path = Path(deny_file)
    if not deny_path.exists():
        return [Finding("G1-05", str(path), None, "skipped: deny list file missing", f"Create {deny_file}", "skipped")]

    names = [n.strip() for n in deny_path.read_text(encoding="utf-8").splitlines() if n.strip()]
    for i, line in enumerate(text.split("\n"), 1):
        for n in names:
            if re.search(rf"\b{re.escape(n)}\b", line, re.IGNORECASE):
                findings.append(Finding("G1-05", str(path), i, f"Client name '{n}' found in catalog", "Remove the client name"))
    return findings

def _check_secrets(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    patterns = [
        (r"ghp_[a-zA-Z0-9]{36}", "Token (ghp_)"),
        (r"sk-[a-zA-Z0-9]{32,}", "API Key"),
        (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "Private Key"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    ]
    for i, line in enumerate(text.split("\n"), 1):
        for pat, name in patterns:
            if re.search(pat, line):
                findings.append(Finding("G1-06", str(path), i, f"Possible {name} found", "Remove the secret and use env vars"))
    return findings

def _check_placeholders(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    for i, line in enumerate(text.split("\n"), 1):
        if "TO" + "DO" in line:
            findings.append(Finding("G1-07", str(path), i, "Placeholder found", "Implement the content"))
        if "FIX" + "ME" in line:
            findings.append(Finding("G1-07", str(path), i, "Placeholder found", "Implement the content"))
        if path.suffix == ".md" and line.strip() == "...":
            findings.append(Finding("G1-07", str(path), i, "Placeholder found", "Write the content"))
        if ("NotImplemented" + "Error") in line and "src/vash/core/interfaces.py" not in str(path).replace("\\", "/"):
            findings.append(Finding("G1-07", str(path), i, "Placeholder found", "Implement the method"))
    return findings

def _check_adr_headings(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return []
    if not str(rel).startswith("decisions/ADR-"):
        return findings
    template = vash_root() / "method" / "templates" / "adr.md"
    if not template.exists():
        return findings
    tmpl_text = template.read_text(encoding="utf-8")
    required = [line.strip() for line in tmpl_text.split("\n") if line.startswith("## ")]
    actual = [line.strip() for line in text.split("\n") if line.startswith("## ")]
    for req in required:
        if req not in actual:
            findings.append(Finding("G1-08", str(path), None, f"Missing ADR section: {req}", "Add the section from the template"))
    return findings

def _check_markdown_links(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    if path.suffix != ".md":
        return findings
    for i, line in enumerate(text.split("\n"), 1):
        for match in re.finditer(r"\]\(([^)]+)\)", line):
            link = match.group(1).strip()
            if link.startswith("http") or link.startswith("#"):
                continue
            target = link.split("#")[0]
            if not target:
                continue
            target_path = (path.parent / target).resolve()
            if not target_path.exists():
                findings.append(Finding("G1-09", str(path), i, f"Broken relative link: {link}", "Fix the link target"))
    return findings

def _check_artifact_code_blocks(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return []
    if not str(rel).startswith("audit/artifacts/") or path.suffix != ".md":
        return findings
    in_block = False
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            if not in_block:
                in_block = True
                lang = line[3:].strip()
                if lang and lang not in ("text", "mermaid"):
                    findings.append(Finding("G1-10", str(path), i, f"Forbidden code block language: {lang}", "Use text or mermaid"))
            else:
                in_block = False
    return findings

def _check_generated_files(path: Path, text: str, repo_root: Path) -> list[Finding]:
    findings = []
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return []
    if str(rel) not in ("CLAUDE.md", "AGENTS.md", "ai-manifest.json"):
        return findings

    try:
        from vash.loader.load import generate_agents_md, generate_claude_md
        from vash.loader.manifest import generate_manifest
    except ImportError:
        return [Finding("G1-12", str(path), None, "skipped: loader not present", "Run after Step 6", "skipped")]

    try:
        if str(rel) in ("CLAUDE.md", "AGENTS.md"):
            expected = generate_claude_md(repo_root) if str(rel) == "CLAUDE.md" else generate_agents_md(repo_root)
            if expected != text:
                findings.append(Finding("G1-12", str(path), None, "Generated file out of sync", "Run vash load"))
        else:
            expected = generate_manifest(repo_root)
            if expected != json.loads(text):
                findings.append(Finding("G1-12", str(path), None, "Generated file out of sync", "Run vash load"))
    except Exception as e:
        findings.append(Finding("G1-12", str(path), None, f"Failed to generate: {e}", "Run vash load"))
    return findings

def _check_skills_and_agents(path: Path, text: str, repo_root: Path) -> list[Finding]:
    """G1-13: skills follow the Agent Skills standard (official skills-ref validator); agents follow VASH's neutral format."""
    from vash.loader.skills import validate_agent, validate_skill

    if path.name == "SKILL.md":
        errors = validate_skill(path.parent)
        if errors is None:
            return [Finding("G1-13", str(path), None, "skipped: skills-ref not installed",
                            "pip install 'vash[skills]'", "skipped")]
        return [Finding("G1-13", str(path), None, e, "Follow the Agent Skills spec (agentskills.io)") for e in errors]
    if path.parent.name == "agents" and path.name != "README.md" and path.suffix == ".md":
        return [Finding("G1-13", str(path), None, e, "Follow method/templates/agent.md") for e in validate_agent(path)]
    return []

RULES = [
    Rule("G1-01", "Formatting", ("*",), _check_format, "Use LF, UTF-8, no BOM, no trailing spaces"),
    Rule("G1-02", "Syntax", ("*.json", "*.toml", "*.py"), _check_syntax, "Fix syntax"),
    Rule("G1-03", "Schema", ("*.json",), _check_schemas, "Fix schema fields"),
    Rule("G1-04", "Vendors", ("*.py",), _check_vendor_names, "Move vendor logic to an adapter"),
    Rule("G1-05", "Client names", ("*.md", "*.json", "*.py", "*.tf", "*.yml"), _check_deny_names, "Remove the client name"),
    Rule("G1-06", "Secrets", ("*",), _check_secrets, "Use env vars"),
    Rule("G1-07", "Placeholders", ("*",), _check_placeholders, "Implement the content"),
    Rule("G1-08", "ADR headings", ("decisions/ADR-*.md",), _check_adr_headings, "Add missing sections"),
    Rule("G1-09", "Markdown links", ("*.md",), _check_markdown_links, "Fix broken links"),
    Rule("G1-10", "Artifact code", ("audit/artifacts/*.md",), _check_artifact_code_blocks, "Use text or mermaid"),
    Rule("G1-12", "Generated files", ("CLAUDE.md", "AGENTS.md", "ai-manifest.json"), _check_generated_files, "Run vash load"),
    Rule("G1-13", "Skills and agents", ("SKILL.md", "*.md"), _check_skills_and_agents, "Follow the Agent Skills spec"),
]

def _load_extra_rules() -> list[Rule]:
    extra = []
    try:
        import vash.adapters
        for _, name, _ in pkgutil.walk_packages(vash.adapters.__path__, "vash.adapters."):
            if name.endswith(".gate1_rules"):
                mod = importlib.import_module(name)
                if hasattr(mod, "RULES"):
                    extra.extend(mod.RULES)
    except ImportError:
        pass
    return extra

def run(paths: Sequence[Path], repo_root: Path, rule_ids: Sequence[str] | None = None) -> Gate1Report:
    """Run Gate 1 rules on the given paths."""
    findings = []
    checked = 0

    all_rules = RULES + _load_extra_rules()
    active_rules = all_rules
    if rule_ids:
        active_rules = [r for r in all_rules if r.id in rule_ids]

    to_check = []
    for p in paths:
        if p.is_dir():
            is_git = False
            try:
                subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=p, check=True, capture_output=True)
                is_git = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            if is_git:
                r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=p, capture_output=True, check=True)
                for name in r.stdout.decode("utf-8").split("\0"):
                    if name:
                        to_check.append((p / name).resolve())
            else:
                for f in p.rglob("*"):
                    if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts:
                        to_check.append(f)
        elif p.is_file():
            to_check.append(p)

    for p in to_check:
        checked += 1
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("G1-01", str(p), None, "Not UTF-8", "Save as UTF-8"))
            continue

        try:
            rel_str = str(p.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
        except ValueError:
            rel_str = str(p).replace("\\", "/")

        for rule in active_rules:
            applies = False
            for pat in rule.applies_to:
                import fnmatch
                if pat == "*":
                    applies = True
                    break
                if "/" in pat:
                    if fnmatch.fnmatch(rel_str, pat):
                        applies = True
                        break
                else:
                    if fnmatch.fnmatch(p.name, pat):
                        applies = True
                        break
            if not applies:
                continue
            findings.extend(rule.check(p, text, repo_root))

    errors = [f for f in findings if f.severity == "error"]
    return Gate1Report(findings=findings, files_checked=checked, ok=len(errors) == 0)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VASH Gate 1")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--rules", help="Comma-separated rule IDs")
    args = parser.parse_args(argv)

    rule_ids = args.rules.split(",") if args.rules else None
    report = run(args.paths, Path.cwd(), rule_ids)

    if args.json:
        out = {
            "ok": report.ok,
            "files_checked": report.files_checked,
            "findings": [
                {"rule": f.rule_id, "path": f.path, "line": f.line, "message": f.message, "fix": f.fix, "severity": f.severity}
                for f in report.findings
            ]
        }
        print(json.dumps(out, indent=2))
    else:
        for f in report.findings:
            loc = f"{f.path}:{f.line}" if f.line else f.path
            print(f"[{f.rule_id}] {loc}: {f.message} -> {f.fix}")
        print(f"\nChecked {report.files_checked} files. {'FAIL' if not report.ok else 'PASS'}")

    return 0 if report.ok else 1

if __name__ == "__main__":
    sys.exit(main())
