"""Validate reviewed release associations against their published Git trees."""

import json
import re
import subprocess
from pathlib import Path

HISTORY_PATH = "plugin-release-history.json"
PUBLIC_FIELDS = ("name", "version", "version_hash")
EVIDENCE_FIELDS = {*PUBLIC_FIELDS, "commit", "validation_run"}


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(f"release history cannot read Git evidence: {result.stderr.strip()}")
    return result.stdout.strip()


def load_history(root: Path, releases: list[dict], baseline: str | None = None) -> list[dict]:
    entries = json.loads((root / HISTORY_PATH).read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("release history must be an array")
    versions: dict[tuple, str] = {}
    hashes: dict[str, tuple] = {}

    def associate(entry: dict) -> tuple:
        name, version, value = (entry.get(field) for field in PUBLIC_FIELDS)
        if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)
                and isinstance(version, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)
                and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{16}", value)):
            raise ValueError("release history has an invalid name, version or hash")
        key = (name, tuple(map(int, version.split("."))))
        if key in versions and versions[key] != value:
            raise ValueError(f"release history has conflicting hashes for {name} {version}")
        if value in hashes and hashes[value] != key:
            raise ValueError(f"release history reuses hash {value}")
        versions[key], hashes[value] = value, key
        return key

    main_commits = set()
    if entries:
        main_commits = set(git(root, "rev-list", "--first-parent", "refs/remotes/origin/main").splitlines())
    history_keys = set()
    documents = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != EVIDENCE_FIELDS:
            raise ValueError("release history entries need name, version, version_hash, commit and validation_run")
        key = associate(entry)
        if key in history_keys:
            raise ValueError("release history repeats an association")
        history_keys.add(key)
        commit, run = entry["commit"], entry["validation_run"]
        if not (isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)
                and commit in main_commits):
            raise ValueError("release history source is not a published main revision")
        if not (isinstance(run, str) and re.fullmatch(
                r"https://github\.com/massdo/massdo-marketplace/actions/runs/[0-9]+", run)):
            raise ValueError("release history needs a validation run URL")
        source = f"{commit}:plugins/{entry['name']}/plugin-release.json"
        if source not in documents:
            documents[source] = json.loads(git(root, "show", source))
        published = documents[source]
        if not isinstance(published, dict) or any(
                published.get(field) != entry[field] for field in ("version", "version_hash")):
            raise ValueError(f"release history disagrees with published source {source}")

    for release in releases:
        associate(release)
    if baseline is not None:
        files = set(git(root, "ls-tree", "-r", "--name-only", baseline).splitlines())
        if HISTORY_PATH in files:
            previous = json.loads(git(root, "show", f"{baseline}:{HISTORY_PATH}"))
            for entry in previous:
                key = (entry["name"], tuple(map(int, entry["version"].split("."))))
                if key not in history_keys or versions[key] != entry["version_hash"]:
                    raise ValueError("release history must preserve previous associations")
        for release in releases:
            path = f"plugins/{release['name']}/plugin-release.json"
            if path not in files:
                continue
            previous = json.loads(git(root, "show", f"{baseline}:{path}"))
            if (previous.get("version"), previous.get("version_hash")) == (
                    release["version"], release["version_hash"]):
                continue
            if not previous.get("version_hash"):
                continue
            key = (release["name"], tuple(map(int, previous["version"].split("."))))
            if key not in history_keys or versions[key] != previous["version_hash"]:
                raise ValueError(f"release history must retain the previous release of {release['name']}")

    return [{field: entry[field] for field in PUBLIC_FIELDS} for entry in entries]
