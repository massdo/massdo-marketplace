#!/usr/bin/env python3

"""Validate the marketplace.

Each plugin under plugins/ is an independent world: it declares itself to
whichever ecosystems it supports, and is validated on its own terms. Nothing
here is indexed by position or hardcoded to a plugin name, so adding a plugin
or reordering a catalog does not break the script.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"

SEMVER = re.compile(r"\d+\.\d+\.\d+")
VERSION_HASH = re.compile(r"[0-9a-f]{16}")

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


def read_json_at(ref: str, path: Path) -> dict | None:
    """Read a tracked file as of ref. None when the ref or the file is absent."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# A release is published by the file tree alone, so every check below reads the
# tree. Comparing a release to the one before it needs the previous commit,
# which only a local hook has: the CI checkout is shallow.
argv = sys.argv[1:]
if argv[:1] == ["--baseline"] and len(argv) == 2:
    BASELINE: str | None = argv[1]
elif not argv:
    BASELINE = None
else:
    raise SystemExit("usage: validate.py [--baseline <git-ref>]")


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

    # Claude Code falls back to the Git commit SHA when a manifest pins no
    # version, so a missing version there would drift from Codex and Cursor,
    # which pin. One shared number releases the three ecosystems at once.
    versions: dict[str, object] = {}
    for ecosystem, manifest in manifests.items():
        check(
            manifest.get("name") == name,
            f"{name}: {ecosystem} manifest declares {manifest.get('name')!r}",
        )
        version = manifest.get("version")
        check(
            isinstance(version, str) and SEMVER.fullmatch(version) is not None,
            f"{name}: {ecosystem} manifest declares version={version!r}, expected semver",
        )
        versions[ecosystem] = version

    check(
        len(set(versions.values())) <= 1,
        f"{name}: manifests disagree on the version: {versions}",
    )

    # A namesake skill is the installable plugin itself. Its hard-coded version
    # and the public changelog document must match the manifests, or a client
    # reports it is current when it is not.
    namesake_skill = plugin / "skills" / name / "SKILL.md"
    if namesake_skill.is_file():
        agreed = next(iter(set(versions.values())), None)
        release_path = plugin / "plugin-release.json"
        release: dict | None = None
        check(
            release_path.is_file(),
            f"{name}: missing plugin-release.json next to the namesake skill",
        )
        if release_path.is_file():
            check(
                release_path.stat().st_size <= 4096,
                f"{name}: plugin-release.json exceeds 4096 bytes",
            )
            try:
                release = read_json(release_path)
            except json.JSONDecodeError as error:
                errors.append(f"{name}: plugin-release.json is not JSON: {error}")
                release = None
            if isinstance(release, dict):
                check(
                    set(release) == {"version", "version_hash", "changelog"},
                    f"{name}: plugin-release.json keys={sorted(release)}, "
                    "expected exactly version, version_hash and changelog",
                )
                check(
                    release.get("version") == agreed,
                    f"{name}: plugin-release.json version={release.get('version')!r}, "
                    f"expected {agreed!r}",
                )
                version_hash = release.get("version_hash")
                check(
                    isinstance(version_hash, str)
                    and VERSION_HASH.fullmatch(version_hash) is not None,
                    f"{name}: plugin-release.json version_hash={version_hash!r}, "
                    "expected 16 lowercase hex characters",
                )
                changelog = release.get("changelog")
                check(
                    isinstance(changelog, str) and changelog.strip() != "",
                    f"{name}: plugin-release.json changelog must be a non-empty string",
                )
                if isinstance(changelog, str):
                    changelog_lines = [
                        line for line in changelog.splitlines() if line.strip() != ""
                    ]
                    check(
                        1 <= len(changelog_lines) <= 3,
                        f"{name}: plugin-release.json changelog has "
                        f"{len(changelog_lines)} non-empty lines, expected 1 to 3",
                    )

                # The changelog is what a client shows for the new version. A
                # bump that keeps the previous text describes the wrong release.
                published = (
                    read_json_at(BASELINE, release_path)
                    if BASELINE is not None
                    else None
                )
                if isinstance(published, dict):
                    check(
                        published.get("version") == release.get("version")
                        or published.get("changelog") != release.get("changelog"),
                        f"{name}: version {published.get('version')!r} becomes "
                        f"{release.get('version')!r} but the changelog is unchanged",
                    )
                    # The hash is what the server compares. A bump that keeps
                    # it tells outdated clients they are current.
                    check(
                        published.get("version") == release.get("version")
                        or published.get("version_hash") != release.get("version_hash"),
                        f"{name}: version {published.get('version')!r} becomes "
                        f"{release.get('version')!r} but version_hash is unchanged "
                        "— regenerate it (openssl rand -hex 8)",
                    )

        skill_text = namesake_skill.read_text(encoding="utf-8")
        frontmatter = re.match(r"^---\n(?P<body>.*?)\n---\n", skill_text, re.DOTALL)
        plugin_version = None
        if frontmatter is not None:
            match = re.search(
                r"^pluginVersion: *(\d+\.\d+\.\d+)$",
                frontmatter.group("body"),
                re.MULTILINE,
            )
            if match is not None:
                plugin_version = match.group(1)
        check(
            plugin_version == agreed,
            f"{name}: namesake skill pluginVersion={plugin_version!r}, "
            f"expected {agreed!r}",
        )

        # A skill hard-codes the hash it sends. A stale one would mark every
        # up-to-date install as outdated.
        published_hash = (
            release.get("version_hash") if isinstance(release, dict) else None
        )
        for skill in sorted(plugin.rglob("SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            if "version_hash" not in text:
                continue
            declared = re.search(r'"version_hash": *"([0-9a-f]{16})"', text)
            where = skill.relative_to(ROOT)
            check(
                declared is not None and declared.group(1) == published_hash,
                f"{where}: version_hash does not match plugin-release.json",
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
