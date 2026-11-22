#!/usr/bin/env python3

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "comments-baseline.json"
SCOPE_DIRECTORIES = (".githooks", "scripts", "tests")
SCOPE_FILES = ("install.sh", "install.ps1", "uninstall.sh")
HASH_SUFFIXES = {".sh", ".ps1", ""}
SLASH_SUFFIXES = {".cs"}
PYTHON_DIRECTIVE = re.compile(r"#\s*(type:|noqa\b|pragma:|fmt:|-\*-|coding[:=])")
HASH_DIRECTIVE = re.compile(r"#\s*shellcheck\b|#requires\b", re.IGNORECASE)
LOWER_COMMAND = "python3 scripts/check_comments.py --lower-baseline"


def scope():
    files = [ROOT / name for name in SCOPE_FILES]
    for directory in SCOPE_DIRECTORIES:
        files += sorted((ROOT / directory).rglob("*"))
    return [
        path for path in files
        if path.is_file() and "__pycache__" not in path.parts
        and (path.suffix == ".py" or path.suffix in SLASH_SUFFIXES
             or (path.suffix in HASH_SUFFIXES
                 and (path.suffix or path.parent.name == ".githooks")))
    ]


def outside_quotes(prefix):
    return prefix.count('"') % 2 == 0 and prefix.count("'") % 2 == 0


def python_comments(source):
    found = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        if line == 1 and token.string.startswith("#!"):
            continue
        if PYTHON_DIRECTIVE.match(token.string):
            continue
        found.append((line, token.string.strip()))
    tree = ast.parse(source)
    lines = source.split("\n")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        first = node.body[0] if node.body else None
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        if isinstance(node, ast.Module) and "__doc__" in source:
            continue
        text = "\n".join(lines[first.lineno - 1:first.end_lineno]).strip()
        found.append((first.lineno, text))
    return found


def marker_comments(source, marker, block, directive):
    found = []
    trailing = re.compile(r"(?<=\s)" + re.escape(marker) + r"\s.*$")
    for number, line in enumerate(source.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith(block):
            found.append((number, stripped))
            continue
        if stripped.startswith(marker):
            if number == 1 and stripped.startswith("#!"):
                continue
            if directive is not None and directive.match(stripped):
                continue
            found.append((number, stripped))
            continue
        match = trailing.search(line)
        if match and outside_quotes(line[:match.start()]):
            found.append((number, match.group(0).strip()))
    return found


def comments(path):
    source = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".py":
        return python_comments(source)
    if path.suffix in SLASH_SUFFIXES:
        return marker_comments(source, "//", "/*", None)
    return marker_comments(source, "#", "<#", HASH_DIRECTIVE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lower-baseline", action="store_true")
    args = parser.parse_args()
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else {}
    found = {}
    for path in scope():
        entries = comments(path)
        if entries:
            found[path.relative_to(ROOT).as_posix()] = entries

    if args.lower_baseline:
        lowered = {}
        for name, allowed in baseline.items():
            present = Counter(text for _, text in found.get(name, []))
            kept = {text: min(count, present[text]) for text, count in allowed.items()
                    if present[text] > 0}
            if kept:
                lowered[name] = kept
        if lowered:
            BASELINE.write_text(json.dumps(lowered, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
        elif BASELINE.is_file():
            BASELINE.unlink()
        print("Comment baseline lowered.")
        return 0

    errors = []
    for name in sorted(set(found) | set(baseline)):
        allowed = Counter(baseline.get(name, {}))
        seen = Counter()
        for line, text in found.get(name, []):
            seen[text] += 1
            if seen[text] > allowed[text]:
                errors.append(f"{name}:{line}: comment not allowed: {text.splitlines()[0]}")
        if any(seen[text] < count for text, count in allowed.items()):
            errors.append(f"{name}: the baseline holds a comment that is gone; run {LOWER_COMMAND}")
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    if errors:
        return 1
    print("Comment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
