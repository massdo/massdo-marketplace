---
name: prune-plugin-cache
description: Delete the stale plugin versions Claude Code leaves in ~/.claude/plugins/cache after an update, which make every skill and command of that plugin appear twice or more in the picker. Use whenever the user reports duplicate slash commands or duplicate skills, sees the same command listed several times with different descriptions, wonders why a plugin appears more than once, or asks to clean up the plugin cache.
---

# Prune the plugin cache

Updating a plugin installs the new version beside the old one and never removes
the old one. Both stay on disk and both keep being loaded, so each skill and
command of that plugin appears once per version in the picker. The symptom the
user sees is duplicate entries, often with slightly different descriptions,
because the older version carries older wording.

`installed_plugins.json` records exactly one `installPath` per installed
plugin. Every other version directory in the cache is an orphan.

## Run it

List first, so the user sees what is about to go:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prune-plugin-cache/scripts/prune_plugin_cache.py"
```

Then delete:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prune-plugin-cache/scripts/prune_plugin_cache.py" --apply
```

Tell the user to run `/reload-plugins` afterwards — the picker keeps the old
entries until the plugins are reloaded.

## What to expect

The cache is disposable: a reinstall re-clones anything deleted here, so this
is safe to run at any time. The script reads the manifest first and stops if it
cannot, rather than treating an unreadable manifest as "nothing is installed"
and deleting the whole cache.

Only `<cache>/<marketplace>/<plugin>/<version>` directories are candidates.

## When duplicates survive the prune

Two entries can remain after the cache is clean, and that is not a bug to fix
here. A plugin that ships both `skills/<name>/SKILL.md` and
`commands/<name>.md` registers two invocables under one name. Tell the user
that this second kind of duplicate is a packaging choice in the plugin itself:
the command usually exists for editors that require a declared `commands/`
directory, while Claude Code already exposes every skill as `/plugin:skill`.
