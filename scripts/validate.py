#!/usr/bin/env python3

"""Validate the marketplace.

Each plugin under plugins/ is an independent world: it declares itself to
whichever ecosystems it supports, and is validated on its own terms. Nothing
here is indexed by position or hardcoded to a plugin name, so adding a plugin
or reordering a catalog does not break the script.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from plugin_release_history import load_history


ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"

SEMVER = re.compile(r"\d+\.\d+\.\d+")
VERSION_HASH = re.compile(r"[0-9a-f]{16}")

# Root catalog -> how that ecosystem spells a plugin's entry name and source
# path. Kimi Code names its entries `id` where the others use `name`.
CATALOGS = {
    "codex": (ROOT / ".agents" / "plugins" / "marketplace.json",
              lambda entry: entry["name"], lambda entry: entry["source"]["path"]),
    "claude": (ROOT / ".claude-plugin" / "marketplace.json",
               lambda entry: entry["name"], lambda entry: entry["source"]),
    "cursor": (ROOT / ".cursor-plugin" / "marketplace.json",
               lambda entry: entry["name"], lambda entry: entry["source"]),
    "kimi": (ROOT / ".kimi-plugin" / "marketplace.json",
             lambda entry: entry["id"], lambda entry: entry["source"]),
}

# Ecosystem -> the manifest a plugin must ship to appear in that catalog.
MANIFESTS = {
    "codex": ".codex-plugin/plugin.json",
    "claude": ".claude-plugin/plugin.json",
    "cursor": ".cursor-plugin/plugin.json",
    "kimi": ".kimi-plugin/plugin.json",
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
    """Read a release from an already resolved commit; allow new plugins."""
    relative = path.relative_to(ROOT).as_posix()
    listed = subprocess.run(
        ["git", "ls-tree", "--name-only", ref, "--", relative],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if not listed.stdout.strip():
        return None
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"FAIL cannot read baseline release {ref}:{relative}")
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit(f"FAIL invalid baseline release {ref}:{relative}: {error}")
    if not isinstance(document, dict):
        raise SystemExit(f"FAIL baseline release {ref}:{relative} must be an object")
    return document


# A release is published by the file tree alone, so every check below reads the
# tree. Resolve the baseline once so a missing commit never disables checks.
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--baseline", metavar="git-ref")
parser.add_argument("--require-release", action="store_true",
                    help="require a version increase for each changed plugin")
args = parser.parse_args()
BASELINE: str | None = args.baseline
if args.require_release and BASELINE is None:
    parser.error("--require-release requires --baseline")

if BASELINE is not None:
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{BASELINE}^{{commit}}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if resolved.returncode != 0:
        raise SystemExit(f"FAIL baseline {BASELINE!r} is not an available commit")
    BASELINE = resolved.stdout.strip()


changed_plugins: set[str] = set()
if args.require_release:
    for command in (
        ["git", "diff", "--name-only", "--no-renames", "-z", BASELINE, "--", "plugins/"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z", "--", "plugins/"],
    ):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        for filename in result.stdout.split("\0"):
            parts = Path(filename).parts
            if len(parts) >= 3 and parts[0] == "plugins":
                changed_plugins.add(parts[1])


plugin_dirs = sorted(p for p in PLUGINS.iterdir() if p.is_dir())
check(plugin_dirs, "plugins/ holds no plugin")

# --- Every catalog entry points at a plugin that exists and can serve it. ----

for ecosystem, (catalog_path, name_of, source_of) in CATALOGS.items():
    catalog = read_json(catalog_path)
    rel = catalog_path.relative_to(ROOT)
    seen: set[str] = set()

    for entry in catalog["plugins"]:
        name = name_of(entry)
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

# Plugin name -> the hash its plugin-release.json publishes. Filled below, read
# by the pass that checks the hashes skills hard-code.
published_hashes: dict[str, str] = {}

for plugin in plugin_dirs:
    name = plugin.name
    manifests = {
        ecosystem: read_json(plugin / relative)
        for ecosystem, relative in MANIFESTS.items()
        if (plugin / relative).is_file()
    }
    check(manifests, f"{name}: no ecosystem manifest, the plugin is unreachable")

    # Claude Code falls back to the Git commit SHA when a manifest pins no
    # version, so a missing version there would drift from Codex, Cursor and
    # Kimi Code, which pin. One shared number releases the four ecosystems
    # at once.
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

    # Every release document agrees with its manifests. The independent style
    # plugin keeps version and changelog without a journal identity hash.
    #
    # The document itself is the trigger, not a namesake skill: nestor-beta
    # publishes a release without shipping a skill named after it. A namesake
    # skill still requires one, since that skill *is* the installable plugin.
    agreed = next(iter(set(versions.values())), None)
    namesake_skill = plugin / "skills" / name / "SKILL.md"
    release_path = plugin / "plugin-release.json"
    release: dict | None = None
    check(
        release_path.is_file() or (name != "massdo-skills" and not namesake_skill.is_file()),
        f"{name}: missing plugin-release.json",
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
            release_keys = {"version", "changelog"}
            if name != "massdo-skills":
                release_keys.add("version_hash")
            check(
                set(release) == release_keys,
                f"{name}: plugin-release.json keys={sorted(release)}, "
                f"expected exactly {', '.join(sorted(release_keys))}",
            )
            check(
                release.get("version") == agreed,
                f"{name}: plugin-release.json version={release.get('version')!r}, "
                f"expected {agreed!r}",
            )
            if name != "massdo-skills":
                version_hash = release.get("version_hash")
                check(
                    isinstance(version_hash, str)
                    and VERSION_HASH.fullmatch(version_hash) is not None,
                    f"{name}: plugin-release.json version_hash={version_hash!r}, "
                    "expected 16 lowercase hex characters",
                )
                if isinstance(version_hash, str):
                    published_hashes[name] = version_hash
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
                if name in changed_plugins:
                    previous_version = published.get("version")
                    current_version = release.get("version")
                    valid_versions = all(
                        isinstance(version, str) and SEMVER.fullmatch(version)
                        for version in (previous_version, current_version)
                    )
                    check(
                        valid_versions
                        and tuple(map(int, current_version.split(".")))
                        > tuple(map(int, previous_version.split("."))),
                        f"{name}: plugin files changed but version must increase "
                        f"from {previous_version!r} (found {current_version!r}); "
                        "update the manifests and release document",
                    )
                check(
                    published.get("version") == release.get("version")
                    or published.get("changelog") != release.get("changelog"),
                    f"{name}: version {published.get('version')!r} becomes "
                    f"{release.get('version')!r} but the changelog is unchanged",
                )
                # The hash is what the server compares. A bump that keeps
                # it tells outdated clients they are current.
                check(
                    name == "massdo-skills"
                    or published.get("version") == release.get("version")
                    or published.get("version_hash") != release.get("version_hash"),
                    f"{name}: version {published.get('version')!r} becomes "
                    f"{release.get('version')!r} but version_hash is unchanged "
                    "— regenerate it (openssl rand -hex 8)",
                )


    if namesake_skill.is_file():
        skill_text = namesake_skill.read_text(encoding="utf-8")
        if name == "nestor":
            # The antipatterns are declared once, as the bullets of the body's
            # `## antipattern` section: the body is what a client injects, and
            # the frontmatter keeps the portable Agent Skills fields only.
            section = re.search(
                r"^## antipattern\n(?P<entries>.*?)(?=^## |\Z)",
                skill_text,
                re.MULTILINE | re.DOTALL,
            )
            check(
                section is not None,
                "nestor: namesake skill has no `## antipattern` section",
            )
            for antipattern in (
                "search_for_known_identity",
                "search_project_for_named_project",
                "get_item_burst",
                "preventive_get_item_before_update",
                "post_success_get_item",
                "stale_version_etag_pair",
                "mixed_version_etag_reads",
            ):
                check(
                    section is not None
                    and re.search(
                        rf"^- `{antipattern}`: \S",
                        section.group("entries"),
                        re.MULTILINE,
                    )
                    is not None,
                    f"nestor: namesake skill omits antipattern {antipattern!r}",
                )
            check(
                "never call `search_items` or `list_items` to reach an item whose id "
                "or slug is already known" in skill_text,
                "nestor: skill does not forbid searching for a known identity",
            )
            check(
                "never call `search_project` to resolve a project the user names"
                in skill_text,
                "nestor: skill does not forbid search_project for a named project",
            )
            check(
                "never call `get_item` immediately before `update_item`" in skill_text,
                "nestor: skill does not forbid the preventive get_item pattern",
            )
            check(
                "never call `get_item` after a successful `update_item`" in skill_text,
                "nestor: skill does not forbid the post-success get_item pattern",
            )
            check(
                "When no valid pair is held, call `update_item` without a precondition."
                in skill_text,
                "nestor: skill does not permit a direct mutation without a held pair",
            )
            check(
                "Take that current item from `details.current` when the conflict includes it."
                in skill_text,
                "nestor: skill does not take the current item from a precondition conflict",
            )
            check(
                "Call `get_item` once only when the rejection has no `details.current`"
                in skill_text,
                "nestor: skill drops the empty-conflict get_item fallback",
            )
        # pluginVersion belongs to this repository, not to Agent Skills, so it
        # lives in the metadata map, whose values are strings.
        frontmatter = re.match(r"^---\n(?P<body>.*?)\n---\n", skill_text, re.DOTALL)
        plugin_version = None
        if frontmatter is not None:
            check(
                re.search(
                    r"^(?:pluginVersion|antipattern):",
                    frontmatter.group("body"),
                    re.MULTILINE,
                )
                is None,
                f"{name}: namesake skill declares a repository field outside metadata",
            )
            metadata = re.search(
                r"^metadata:[ \t]*\n(?P<entries>(?:[ \t]+\S.*(?:\n|\Z))+)",
                frontmatter.group("body"),
                re.MULTILINE,
            )
            if metadata is not None:
                match = re.search(
                    r'^[ \t]+pluginVersion: *"(\d+\.\d+\.\d+)"[ \t]*$',
                    metadata.group("entries"),
                    re.MULTILINE,
                )
                if match is not None:
                    plugin_version = match.group(1)
        check(
            plugin_version == agreed,
            f"{name}: namesake skill metadata.pluginVersion={plugin_version!r}, "
            f'expected "{agreed}" as a quoted string',
        )


    # A path a manifest declares must resolve, or the ecosystem loads nothing.
    for ecosystem, manifest in manifests.items():
        for key in ("skills", "commands", "mcpServers", "hooks", "agents", "rules"):
            value = manifest.get(key)
            # Kimi Code declares mcpServers as an inline server map, not as
            # a path to a file the way Codex and Cursor do.
            if isinstance(value, dict):
                continue
            for declared in [value] if isinstance(value, str) else (value or []):
                if not isinstance(declared, str):
                    continue
                check(
                    (plugin / declared).exists(),
                    f"{name}: {ecosystem} manifest declares {key}={declared}, missing",
                )

    # A skill is reached one way: by its own name. A command wrapper that
    # inlines a skill gives the same instructions a second entry point, which
    # Claude Code then counts twice in the menu and in `plugin details`, while
    # Codex never sees it at all. The directory is checked too: Cursor and
    # Claude Code find commands by convention, so dropping the declaration
    # without dropping the files would quietly restore the duplicate.
    for ecosystem, manifest in manifests.items():
        check(
            manifest.get("commands") is None,
            f"{name}: {ecosystem} manifest declares commands — a skill is "
            "invoked by its own name, so the wrapper surface is gone",
        )
    check(
        not (plugin / "commands").exists(),
        f"{name}: ships a commands/ directory — a wrapper duplicates the skill "
        "it inlines instead of adding a surface",
    )

    # Cursor reads mcp.json, Claude Code and Codex read .mcp.json. Two files,
    # one server: a drift here sends one ecosystem at a dead endpoint.
    dotted, plain = plugin / ".mcp.json", plugin / "mcp.json"
    if dotted.is_file() and plain.is_file():
        check(
            read_json(dotted) == read_json(plain),
            f"{name}: .mcp.json and mcp.json have diverged",
        )

    # Kimi Code declares its MCP servers inline in its manifest instead of
    # pointing at a file. Same server, same URL, same drift to catch.
    kimi_manifest = manifests.get("kimi")
    if kimi_manifest is not None and plain.is_file():
        declared = kimi_manifest.get("mcpServers") or {}
        for server, config in (read_json(plain).get("mcpServers") or {}).items():
            check(
                declared.get(server, {}).get("url") == config.get("url"),
                f"{name}: kimi manifest mcpServers.{server} declares "
                f"url={declared.get(server, {}).get('url')!r}, "
                f"mcp.json has {config.get('url')!r}",
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
        # Agent Skills requires the declared name to be the directory name,
        # and every client resolves an invocation through the directory. A
        # mismatch makes `/<plugin>:<name>` reach nothing while the skill
        # still looks present.
        if declared is not None:
            by_name.setdefault(declared.group("name"), []).append(str(where))
            check(
                declared.group("name") == skill.parent.name,
                f"{where}: declares name={declared.group('name')!r} inside "
                f"{skill.parent.name}/ — the two must be the same",
            )

        # user-invocable: false hides a skill from the menu, and together with
        # disable-model-invocation nothing can reach it any more. Neither is a
        # portable field, and this repository uses the second one alone.
        check(
            re.search(r"^user-invocable:", metadata, re.MULTILINE) is None,
            f"{where}: declares user-invocable — with disable-model-invocation "
            "it leaves the skill unreachable, so the repository never sets it",
        )

    for skill_name, paths in by_name.items():
        check(
            len(paths) == 1,
            f"{name}: skill {skill_name!r} is defined {len(paths)} times: {paths}",
        )

# --- Journal-integrated skills declare their plugin's identity. ------------

# The prefix preserves plugin identity after the published hash changes.
# Other plugins keep their existing unprefixed contract.
plugin_hash_prefixes = {"nestor": "1", "nestor-beta": "2"}
for plugin in plugin_dirs:
    name = plugin.name
    if name == "massdo-skills":
        for resource in sorted(plugin.rglob("*")):
            if resource.is_file():
                content = resource.read_text(encoding="utf-8", errors="ignore")
                check(
                    re.search(r"nestor|version_hash|journal\.mcp-marketplace\.org",
                              str(resource.relative_to(plugin)) + "\n" + content, re.I) is None,
                    f"{resource.relative_to(ROOT)}: standalone plugin must not "
                    "reference Nestor or version_hash",
                )
        continue
    for skill in sorted(plugin.rglob("SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        where = skill.relative_to(ROOT)
        declared = re.search(r'"version_hash": *"([12]?[0-9a-f]{16})"', text)
        if declared is None:
            errors.append(
                f"{where}: declares no version_hash — no skill is accepted "
                f"without the hash of {name}/plugin-release.json"
            )
            continue
        if name not in published_hashes:
            errors.append(
                f"{where}: {name} publishes no plugin-release.json, so its "
                "version_hash matches no release"
            )
            continue
        check(
            declared.group(1) == plugin_hash_prefixes.get(name, "") + published_hashes[name],
            f"{where}: version_hash does not match {name}/plugin-release.json",
        )

# Nestor examples are executable input shapes, even though this repository
# ships no MCP implementation. Catch obsolete tools and malformed conditional
# reads in every distributed Markdown resource, including references.
for name in ("nestor", "nestor-beta"):
    for resource in sorted((PLUGINS / name).rglob("*.md")):
        text = resource.read_text(encoding="utf-8")
        where = resource.relative_to(ROOT)
        check("get_item_version" not in text,
              f"{where}: obsolete get_item_version instruction")
        for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
            try:
                example = json.loads(block)
            except json.JSONDecodeError:
                check(False, f"{where}: invalid JSON example")
                continue
            if not isinstance(example, dict):
                continue
            if example.get("unchanged") is True:
                check(not ({"item", "title", "body", "tags", "relations", "etag"} & example.keys()),
                      f"{where}: unchanged example must not repeat content or ETag")
            if "ref" not in example:
                continue
            check("known" in example, f"{where}: get_item example omits known")
            refs, known = example["ref"], example.get("known")
            pairs = [known]
            if isinstance(refs, list):
                check(1 <= len(refs) <= 5, f"{where}: get_item example needs 1 to 5 refs")
                check(all(isinstance(ref, str) for ref in refs),
                      f"{where}: get_item refs must be strings")
                check(isinstance(known, list) and len(known) == len(refs),
                      f"{where}: known must align with ref position by position")
                pairs = known if isinstance(known, list) else []
            else:
                check(isinstance(refs, str), f"{where}: get_item ref must be a string or array")
            for pair in pairs:
                check(pair is None or (
                    isinstance(pair, dict) and set(pair) == {"version", "etag"}
                    and type(pair["version"]) is int and pair["version"] >= 1
                    and isinstance(pair["etag"], str) and bool(pair["etag"])
                ), f"{where}: known needs null or a complete version/ETag pair")
            check(example.get("version_hash") == plugin_hash_prefixes[name] + published_hashes.get(name, ""),
                  f"{where}: get_item example version_hash does not match its plugin release")

# --- Verified release history. --------------------------------------------

try:
    releases = [{"name": plugin.name, **read_json(plugin / "plugin-release.json")}
                for plugin in plugin_dirs if (plugin / "plugin-release.json").is_file()]
    load_history(ROOT, releases, BASELINE)
except (OSError, ValueError, TypeError, KeyError) as error:
    errors.append(f"release history: {error}")

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
