#!/usr/bin/env python3
"""VASH step runner. Reads a step bundle and applies it.

Bundle format (UTF-8, LF):
  Line 1:  # VASH step <N> bundle
  Header:  key: value (allowed keys: requires, allowed_write, verify_roots,
           forbidden_after, min_bytes). Repeatable. # and blank lines skipped.
  Blocks (start with "=== "):
    === MOVE <src> -> <dst>
    === REPLACE <old> -> <new>
    === AMEND <path>
    --- old
    <text>
    --- new
    <text>
    === PATCH <path>
    --- old
    <text>
    --- new
    <text>
    === FILE <path>
    <verbatim content>
    === END (last non-empty line)

Moved files: lone CR and CRLF become LF, then trailing spaces are removed,
before REPLACE and AMEND.

Usage:  python tools/vash_build.py <bundle.md> [--check]

Exit codes:
    0  success
    1  any check failed (bundle structure, content, verify)
    17 path not allowed (WriteNotAllowed)
"""
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


HEADER_KEYS = {"requires", "allowed_write", "verify_roots", "forbidden_after", "min_bytes"}


class BundleError(Exception):
    def __init__(self, line_no, message):
        self.line_no = line_no
        self.message = message
        super().__init__(f"line {line_no}: {message}")


class PathNotAllowed(Exception):
    pass


def _normalize(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.rstrip("\n") + "\n"


def _check_path(p):
    if p.startswith("/"):
        raise PathNotAllowed(f"absolute path: {p}")
    if ".." in p.split("/"):
        raise PathNotAllowed(f"path traversal: {p}")
    if p == ".git" or p.startswith(".git/") or "/.git/" in p:
        raise PathNotAllowed(f"path inside .git: {p}")


def _matches_allowed(p, allowed):
    if not allowed:
        return False
    for pat in allowed:
        if "**" in pat:
            regex = "^" + re.escape(pat).replace(r"\*\*", ".*") + "$"
            if re.match(regex, p):
                return True
        if fnmatch.fnmatch(p, pat):
            return True
    return False


def parse_bundle(path):
    raw = Path(path).read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    raw = raw.replace("\r\n", "\n")
    lines = raw.split("\n")

    if not lines or not lines[0].startswith("# VASH step ") or not lines[0].endswith(" bundle"):
        raise BundleError(1, "line 1 must be '# VASH step <N> bundle'")

    header = {k: [] for k in HEADER_KEYS}

    i = 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("=== "):
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in line:
            raise BundleError(i + 1, "header line must be 'key: value'")
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key not in HEADER_KEYS:
            raise BundleError(i + 1, f"unknown header key: {key}")
        if key == "min_bytes":
            parts = value.rsplit(" ", 1)
            if len(parts) != 2:
                raise BundleError(i + 1, "min_bytes must be '<path> <integer>'")
            try:
                header["min_bytes"].append((parts[0].strip(), int(parts[1].strip())))
            except ValueError:
                raise BundleError(i + 1, "min_bytes integer is invalid")
        else:
            header[key].append(value)
        i += 1

    blocks = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if not line.startswith("=== "):
            raise BundleError(i + 1, "unexpected content outside a block")

        marker = line[4:].strip()
        marker_line = i + 1

        if marker == "END":
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    raise BundleError(j + 1, "content after === END")
            return header, blocks

        if marker.startswith("MOVE "):
            rest = marker[5:]
            if " -> " not in rest:
                raise BundleError(marker_line, "MOVE must be 'MOVE <src> -> <dst>'")
            src, _, dst = rest.partition(" -> ")
            blocks.append({"type": "move", "src": src.strip(), "dst": dst.strip(), "line": marker_line})
            i += 1
            continue

        if marker.startswith("REPLACE "):
            rest = marker[8:]
            if " -> " not in rest:
                raise BundleError(marker_line, "REPLACE must be 'REPLACE <old> -> <new>'")
            old, _, new = rest.partition(" -> ")
            blocks.append({"type": "replace", "old": old.strip(), "new": new.strip(), "line": marker_line})
            i += 1
            continue

        if marker.startswith("AMEND ") or marker.startswith("PATCH "):
            btype = "amend" if marker.startswith("AMEND ") else "patch"
            path_val = marker[6:].strip()
            i += 1
            if i >= len(lines) or lines[i].strip() != "--- old":
                raise BundleError(i + 1, f"{btype.upper()} block must start with '--- old'")
            i += 1
            old_lines = []
            while i < len(lines) and lines[i].strip() != "--- new":
                if lines[i].strip() == "--- old":
                    raise BundleError(i + 1, "duplicate '--- old' in block")
                old_lines.append(lines[i])
                i += 1
            if i >= len(lines):
                raise BundleError(i + 1, f"{btype.upper()} block missing '--- new'")
            i += 1
            new_lines = []
            while i < len(lines) and not lines[i].startswith("=== "):
                if lines[i].strip() == "--- new":
                    raise BundleError(i + 1, "duplicate '--- new' in block")
                new_lines.append(lines[i])
                i += 1
            while old_lines and old_lines[-1] == "":
                old_lines.pop()
            while new_lines and new_lines[-1] == "":
                new_lines.pop()
            if not old_lines:
                raise BundleError(marker_line, f"{btype.upper()} old text is empty")
            if not new_lines:
                raise BundleError(marker_line, f"{btype.upper()} new text is empty")
            blocks.append({
                "type": btype,
                "path": path_val,
                "old": "\n".join(old_lines),
                "new": "\n".join(new_lines),
                "line": marker_line,
            })
            continue

        if marker.startswith("FILE "):
            path_val = marker[5:].strip()
            i += 1
            content_lines = []
            while i < len(lines) and not lines[i].startswith("=== "):
                content_lines.append(lines[i])
                i += 1
            while content_lines and content_lines[-1] == "":
                content_lines.pop()
            if not content_lines:
                raise BundleError(marker_line, "FILE block is empty")
            content = "\n".join(content_lines) + "\n"
            blocks.append({"type": "file", "path": path_val, "content": content, "line": marker_line})
            continue

        raise BundleError(marker_line, f"unknown block type: {marker}")

    raise BundleError(len(lines), "=== END is missing")


def validate_paths(header, blocks):
    all_paths = []
    for b in blocks:
        if b["type"] == "file":
            all_paths.append((b["path"], b["line"], "FILE"))
        elif b["type"] == "move":
            all_paths.append((b["src"], b["line"], "MOVE src"))
            all_paths.append((b["dst"], b["line"], "MOVE dst"))
        elif b["type"] in ("amend", "patch"):
            all_paths.append((b["path"], b["line"], b["type"].upper()))

    for path_val, line_no, kind in all_paths:
        try:
            _check_path(path_val)
        except PathNotAllowed as e:
            raise PathNotAllowed(f"line {line_no}: {kind} {path_val}: {e}")

    has_write_ops = any(b["type"] in ("move", "file", "patch", "amend") for b in blocks)
    allowed = header["allowed_write"]
    if has_write_ops and not allowed:
        raise PathNotAllowed("no allowed_write")

    if not allowed:
        return

    file_targets = set()
    for b in blocks:
        if b["type"] == "file":
            if b["path"] in file_targets:
                raise BundleError(b["line"], f"duplicate FILE path: {b['path']}")
            file_targets.add(b["path"])
            if not _matches_allowed(b["path"], allowed):
                raise PathNotAllowed(f"line {b['line']}: FILE {b['path']}: not in allowed_write")
        elif b["type"] == "move":
            if b["dst"] in file_targets:
                raise BundleError(b["line"], f"duplicate MOVE target: {b['dst']}")
            file_targets.add(b["dst"])
            if not _matches_allowed(b["dst"], allowed):
                raise PathNotAllowed(f"line {b['line']}: MOVE dst {b['dst']}: not in allowed_write")
        elif b["type"] in ("amend", "patch"):
            if not _matches_allowed(b["path"], allowed):
                raise PathNotAllowed(f"line {b['line']}: {b['type'].upper()} {b['path']}: not in allowed_write")


def _has_empty_heading(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines):
            return i + 1
        nxt = lines[j]
        if nxt.startswith("### "):
            continue
        if nxt.startswith("## ") or nxt.startswith("# "):
            return i + 1
    return None


def _check_content(path_str, text, header, raw_checked=False):
    errors = []
    if not raw_checked:
        if text.startswith("\ufeff"):
            errors.append(f"{path_str}: BOM")
        if "\r\n" in text:
            errors.append(f"{path_str}: CRLF")
    if text and not text.endswith("\n"):
        errors.append(f"{path_str}: no final newline")
    if text.endswith("\n\n"):
        errors.append(f"{path_str}: more than one final newline")
    for i, line in enumerate(text.split("\n"), 1):
        if line.rstrip() != line:
            errors.append(f"{path_str}:{i}: trailing spaces")
            break
    bad = _has_empty_heading(text)
    if bad:
        errors.append(f"{path_str}:{bad}: empty ## heading")
    for forb in header["forbidden_after"]:
        if forb in text:
            errors.append(f"{path_str}: contains forbidden '{forb}'")
    for p, minb in header["min_bytes"]:
        if p == path_str:
            size = len(text.encode("utf-8"))
            if size < minb:
                errors.append(f"{path_str}: {size} < min {minb}")
    if path_str.endswith(".json"):
        try:
            data = json.loads(text)
        except Exception as e:
            errors.append(f"{path_str}: invalid JSON: {e}")
            return errors
        if path_str.endswith(".schema.json"):
            if not HAS_JSONSCHEMA:
                errors.append("jsonschema not installed - pip install jsonschema")
                return errors
            try:
                jsonschema.Draft202012Validator.check_schema(data)
            except jsonschema.SchemaError as e:
                errors.append(f"{path_str}: invalid schema: {e.message}")
    return errors


def plan(bundle_path):
    header, blocks = parse_bundle(bundle_path)
    validate_paths(header, blocks)

    errors = []
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True, check=True)
        if r.stdout.strip() != "true":
            errors.append("not a git work tree")
    except (subprocess.CalledProcessError, FileNotFoundError):
        errors.append("not a git work tree")

    for p in header["requires"]:
        if not Path(p).exists():
            errors.append(f"required path missing: {p}")

    move_targets = {str(Path(b["dst"])) for b in blocks if b["type"] == "move"}
    for b in blocks:
        if b["type"] == "amend" and str(Path(b["path"])) not in move_targets:
            errors.append(f"line {b['line']}: AMEND {b['path']} is not a MOVE target")

    bundle_paths = set()
    for b in blocks:
        if b["type"] == "file":
            bundle_paths.add(str(Path(b["path"])))
        elif b["type"] == "move":
            bundle_paths.add(str(Path(b["dst"])))
    for p, minb in header["min_bytes"]:
        if str(Path(p)) not in bundle_paths:
            errors.append(f"min_bytes path not in bundle: {p}")

    if errors:
        return header, blocks, [], {}, errors

    replaces = [(b["old"], b["new"]) for b in blocks if b["type"] == "replace"]
    amendments_by_path = {}
    for b in blocks:
        if b["type"] == "amend":
            amendments_by_path.setdefault(str(Path(b["path"])), []).append(b)

    actions = []
    pending_text = {}

    for b in blocks:
        if b["type"] != "move":
            continue
        sp, dp = Path(b["src"]), Path(b["dst"])
        if sp.exists() and not dp.exists():
            try:
                raw = sp.read_bytes()
                original = raw.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"line {b['line']}: MOVE {b['src']}: not UTF-8")
                continue
            except OSError:
                errors.append(f"line {b['line']}: MOVE {b['src']}: cannot read")
                continue
            is_new = True
            n_lone_cr = raw.count(b"\r") - raw.count(b"\r\n")
            if n_lone_cr > 0:
                actions.append(("lone CR as line break", str(sp), f"{n_lone_cr}"))
        elif dp.exists() and not sp.exists():
            try:
                raw = dp.read_bytes()
                original = raw.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"line {b['line']}: MOVE target {b['dst']}: not UTF-8")
                continue
            except OSError:
                errors.append(f"line {b['line']}: MOVE target {b['dst']}: cannot read")
                continue
            is_new = False
        else:
            errors.append(f"line {b['line']}: MOVE {b['src']} -> {b['dst']}: source/target conflict")
            continue

        amendments = amendments_by_path.get(str(dp), [])

        normalized_original = original.replace("\r\n", "\n").replace("\r", "\n")
        current = _normalize(normalized_original)
        for old, new in replaces:
            current = current.replace(old, new)

        amendments_ok = True
        for amend in amendments:
            old = amend["old"]
            new = amend["new"]
            if new in current:
                actions.append(("already amended", str(dp), f"line {amend['line']}"))
                continue
            count = current.count(old)
            if count != 1:
                errors.append(f"line {amend['line']}: AMEND {dp}: old text appears {count} times (expected 1)")
                amendments_ok = False
                continue
            current = current.replace(old, new)
            actions.append(("amend", str(dp), f"line {amend['line']}"))

        if not amendments_ok:
            continue

        once = _normalize(current)

        twice = once
        for old, new in replaces:
            twice = twice.replace(old, new)
        for amend in amendments:
            old = amend["old"]
            new = amend["new"]
            if new in twice:
                continue
            if twice.count(old) == 1:
                twice = twice.replace(old, new)
        twice = _normalize(twice)

        if once != twice:
            errors.append(f"{dp}: transform is not idempotent")
            continue

        errors.extend(_check_content(str(dp), once, header))
        pending_text[str(dp)] = once
        actions.append(("move" if is_new else "already moved", b["src"], b["dst"]))

    for b in blocks:
        if b["type"] != "patch":
            continue
        p = Path(b["path"])
        if not p.exists():
            errors.append(f"line {b['line']}: PATCH target missing: {p}")
            continue
        try:
            c = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"line {b['line']}: PATCH {p}: not UTF-8")
            continue
        if b["new"] in c:
            actions.append(("already patched", str(p), ""))
        elif c.count(b["old"]) == 1:
            patched = c.replace(b["old"], b["new"])
            errors.extend(_check_content(str(p), patched, header))
            actions.append(("patch", str(p), ""))
        else:
            errors.append(f"line {b['line']}: PATCH {p}: old appears {c.count(b['old'])} times (expected 1)")

    for b in blocks:
        if b["type"] != "file":
            continue
        p = Path(b["path"])
        content = _normalize(b["content"])
        if p.exists():
            current_bytes = p.read_bytes()
            if current_bytes == content.encode("utf-8"):
                actions.append(("unchanged", str(p), ""))
            else:
                errors.append(f"line {b['line']}: FILE {p}: exists with different content")
        else:
            pending_text[str(p)] = content
            errors.extend(_check_content(str(p), content, header))
            actions.append(("create", str(p), ""))

    return header, blocks, actions, pending_text, errors


def apply(header, blocks, actions, pending_text):
    for b in blocks:
        if b["type"] == "move":
            sp, dp = Path(b["src"]), Path(b["dst"])
            if sp.exists() and not dp.exists():
                dp.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "mv", b["src"], b["dst"]], check=True, capture_output=True)

    for b in blocks:
        if b["type"] == "move":
            key = str(Path(b["dst"]))
            if key in pending_text:
                p = Path(key)
                new_content = pending_text[key]
                new_bytes = new_content.encode("utf-8")
                if not p.exists() or p.read_bytes() != new_bytes:
                    p.write_text(new_content, encoding="utf-8", newline="\n")

    for b in blocks:
        if b["type"] == "patch":
            p = Path(b["path"])
            c = p.read_text(encoding="utf-8")
            if b["new"] not in c:
                p.write_text(c.replace(b["old"], b["new"]), encoding="utf-8", newline="\n")

    for b in blocks:
        if b["type"] == "file":
            p = Path(b["path"])
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(_normalize(b["content"]), encoding="utf-8", newline="\n")


def verify(header, blocks):
    errors = []
    paths = set()
    for b in blocks:
        if b["type"] == "file":
            paths.add(str(Path(b["path"])))
        elif b["type"] == "move":
            paths.add(str(Path(b["dst"])))
        elif b["type"] == "patch":
            paths.add(str(Path(b["path"])))

    for root in header["verify_roots"]:
        if not Path(root).exists():
            continue
        r = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", root],
            capture_output=True, check=True)
        for name in r.stdout.decode("utf-8").split("\0"):
            if name and Path(name).is_file():
                paths.add(str(Path(name)))

    for path_str in paths:
        p = Path(path_str)
        if not p.exists():
            errors.append(f"{path_str}: missing after apply")
            continue
        try:
            raw = p.read_bytes()
        except OSError as e:
            errors.append(f"{path_str}: cannot read: {e}")
            continue
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{path_str}: BOM")
        if b"\r\n" in raw:
            errors.append(f"{path_str}: CRLF")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path_str}: not UTF-8")
            continue
        errors.extend(_check_content(path_str, text, header, raw_checked=True))
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/vash_build.py <bundle.md> [--check]")
        return 1
    bundle_path = sys.argv[1]
    check = "--check" in sys.argv

    try:
        header, blocks, actions, pending_text, errors = plan(bundle_path)
    except BundleError as e:
        print(f"Bundle error: {e}")
        return 1
    except PathNotAllowed as e:
        print(f"Path not allowed: {e}")
        return 17

    if errors:
        for e in errors:
            print(f"! {e}")
        return 1

    for kind, p, extra in actions:
        print(f"  {kind} {p}" + (f" ({extra})" if extra else ""))

    if check:
        return 0

    apply(header, blocks, actions, pending_text)

    print()
    errors = verify(header, blocks)
    if errors:
        for e in errors:
            print(f"! {e}")
        return 1
    print("All clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
