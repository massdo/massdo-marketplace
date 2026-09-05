#!/usr/bin/env python3

"""Delete the plugin versions Claude Code left behind in its cache.

Updating a plugin installs the new version next to the old one and never
removes the old one. Both keep being loaded, so every skill and command in that
plugin shows up twice in the picker, once per version on disk.

`installed_plugins.json` records exactly one installPath per installed plugin.
Any other version directory in the cache is an orphan: nothing points at it.

The cache is disposable — a reinstall re-clones whatever is deleted here — but
this script still refuses to guess. It reads the manifest first and stops if it
cannot, rather than deleting on an empty set of active paths.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


CACHE = Path.home() / ".claude" / "plugins" / "cache"
MANIFEST = Path.home() / ".claude" / "plugins" / "installed_plugins.json"


def active_paths() -> set[Path]:
    """Every installPath the manifest declares. Raises rather than return {}."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {
        Path(install["installPath"]).resolve()
        for entries in manifest.get("plugins", {}).values()
        for install in entries
        if isinstance(install, dict) and "installPath" in install
    }
    if not paths:
        raise SystemExit(
            f"{MANIFEST} declares no installPath — refusing to treat every "
            "cached version as an orphan."
        )
    return paths


def orphans(active: set[Path]) -> list[Path]:
    """Cached version directories no installed plugin points at.

    Only <cache>/<marketplace>/<plugin>/<version> is considered, so a stray
    file or a deeper directory is never a candidate.
    """
    found = []
    for marketplace in sorted(p for p in CACHE.iterdir() if p.is_dir()):
        for plugin in sorted(p for p in marketplace.iterdir() if p.is_dir()):
            for version in sorted(p for p in plugin.iterdir() if p.is_dir()):
                if version.resolve() not in active:
                    found.append(version)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete the orphans; without it they are only listed",
    )
    args = parser.parse_args()

    if not CACHE.is_dir():
        print(f"No plugin cache at {CACHE}, nothing to do.")
        return 0

    found = orphans(active_paths())
    if not found:
        print("No orphaned plugin version in the cache.")
        return 0

    for version in found:
        label = f"{version.parent.parent.name}/{version.parent.name}/{version.name}"
        if args.apply:
            shutil.rmtree(version)
            print(f"removed {label}")
        else:
            print(f"orphan  {label}")

    if not args.apply:
        print(f"\n{len(found)} orphan(s). Re-run with --apply to delete them.")
    else:
        print(f"\n{len(found)} orphan(s) removed. Run /reload-plugins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
