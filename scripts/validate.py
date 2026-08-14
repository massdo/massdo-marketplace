#!/usr/bin/env python3

"""Validate the marketplace.

Each plugin under plugins/ is an independent world: it declares itself to
whichever ecosystems it supports, and is validated on its own terms. Nothing
here is indexed by position or hardcoded to a plugin name, so adding a plugin
or reordering a catalog does not break the script.
"""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"

# Root catalog -> how that ecosystem spells a plugin's source path.
CATALOGS = {
    "codex": (ROOT / ".agents" / "plugins" / "marketplace.json",
              lambda entry: entry["source"]["path"]),
    "claude": (ROOT / ".claude-plugin" / "marketplace.json",
               lambda entry: entry["source"]),
    "cursor": (ROOT / ".cursor-plugin" / "marketplace.json",
               lambda entry: entry["source"]),
}

# Ecosystem -> the manifest a plugin must ship to appear in that catalog.
MANIFESTS = {
    "codex": ".codex-plugin/plugin.json",
    "claude": ".claude-plugin/plugin.json",
    "cursor": ".cursor-plugin/plugin.json",
}

# Codex parses its catalog into a Rust enum: an unknown variant rejects the
# whole file, so the marketplace stops being addable at all.
# codex-rs/core-plugins/src/marketplace.rs
CODEX_POLICY = {
    "installation": {"AVAILABLE", "NOT_AVAILABLE"},
    "authentication": {"ON_INSTALL", "ON_USE"},
}

errors: list[str] = []


def check(condition: object, message: str) -> None:
    if not condition:
        errors.append(message)


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


plugin_dirs = sorted(p for p in PLUGINS.iterdir() if p.is_dir())
check(plugin_dirs, "plugins/ holds no plugin")

# --- Every catalog entry points at a plugin that exists and can serve it. ----

for ecosystem, (catalog_path, source_of) in CATALOGS.items():
    catalog = read_json(catalog_path)
    rel = catalog_path.relative_to(ROOT)
    seen: set[str] = set()

    for entry in catalog["plugins"]:
        name = entry["name"]
        check(name not in seen, f"{rel}: {name} listed twice")
        seen.add(name)

        source = source_of(entry)
        check(
            source == f"./plugins/{name}",
            f"{rel}: {name} points at {source}, expected ./plugins/{name}",
        )

        plugin = PLUGINS / name
        check(plugin.is_dir(), f"{rel}: {name} has no directory under plugins/")
        if not plugin.is_dir():
            continue

        manifest = plugin / MANIFESTS[ecosystem]
        check(
            manifest.is_file(),
            f"{rel}: {name} is listed but ships no {MANIFESTS[ecosystem]}",
        )

        if ecosystem == "codex":
            for key, allowed in CODEX_POLICY.items():
                value = entry.get("policy", {}).get(key)
                check(
                    value is None or value in allowed,
                    f"{rel}: {name} policy.{key}={value!r}, expected one of "
                    f"{sorted(allowed)} — an unknown value rejects the catalog",
                )

# --- Each plugin is internally coherent. ------------------------------------

for plugin in plugin_dirs:
    name = plugin.name
    manifests = {
        ecosystem: read_json(plugin / relative)
        for ecosystem, relative in MANIFESTS.items()
        if (plugin / relative).is_file()
    }
    check(manifests, f"{name}: no ecosystem manifest, the plugin is unreachable")

    for ecosystem, manifest in manifests.items():
        check(
            manifest.get("name") == name,
            f"{name}: {ecosystem} manifest declares {manifest.get('name')!r}",
        )
        # Claude Code falls back to the Git commit SHA, so pinning a version
        # here would freeze every install at a stale number.
        if ecosystem == "claude":
            check(
                "version" not in manifest,
                f"{name}: the Claude manifest must not pin a version",
            )

    # A path a manifest declares must resolve, or the ecosystem loads nothing.
    for ecosystem, manifest in manifests.items():
        for key in ("skills", "commands", "mcpServers", "hooks", "agents", "rules"):
            value = manifest.get(key)
            for declared in [value] if isinstance(value, str) else (value or []):
                if not isinstance(declared, str):
                    continue
                check(
                    (plugin / declared).exists(),
                    f"{name}: {ecosystem} manifest declares {key}={declared}, missing",
                )

    # Cursor reads mcp.json, Claude Code and Codex read .mcp.json. Two files,
    # one server: a drift here sends one ecosystem at a dead endpoint.
    dotted, plain = plugin / ".mcp.json", plugin / "mcp.json"
    if dotted.is_file() and plain.is_file():
        check(
            read_json(dotted) == read_json(plain),
            f"{name}: .mcp.json and mcp.json have diverged",
        )

    # Skills are shared by reference across ecosystems, never copied. Two
    # SKILL.md claiming one name inside a plugin means a stale duplicate.
    by_name: dict[str, list[str]] = {}
    for skill in sorted(plugin.rglob("SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        frontmatter = re.match(r"^---\n(?P<body>.*?)\n---\n", text, re.DOTALL)
        where = skill.relative_to(ROOT)
        check(frontmatter is not None, f"{where}: frontmatter is missing")
        if frontmatter is None:
            continue

        metadata = frontmatter.group("body")
        declared = re.search(r"^name: *(?P<name>\S+)$", metadata, re.MULTILINE)
        check(declared is not None, f"{where}: frontmatter declares no name")
        check(
            re.search(r"^description: .+", metadata, re.MULTILINE) is not None,
            f"{where}: frontmatter declares no description",
        )
        if declared is not None:
            by_name.setdefault(declared.group("name"), []).append(str(where))

    for skill_name, paths in by_name.items():
        check(
            len(paths) == 1,
            f"{name}: skill {skill_name!r} is defined {len(paths)} times: {paths}",
        )

# --- Crude secret guard. ----------------------------------------------------

bearer_header = "Authorization:" + " Bearer"
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    content = path.read_text(encoding="utf-8", errors="ignore")
    check(bearer_header not in content, f"Secret-like header in {path}")

if errors:
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"Validation passed for {len(plugin_dirs)} plugins.")
