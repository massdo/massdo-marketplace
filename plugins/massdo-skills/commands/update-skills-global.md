---
description: Update a skill from the massdo marketplace globally, for Codex, Claude Code and Cursor.
argument-hint: "[skill-name]"
allowed-tools: Bash(npx:*)
---

Update the skill `$1` from the `massdo/massdo-marketplace` repository, globally, for Codex, Claude Code and Cursor.

## No skill name given

When `$1` is empty, list what the marketplace currently offers, then ask which one to update:

```bash
npx --yes skills@latest add massdo/massdo-marketplace --list
```

This reads the remote repository without installing anything and without cloning it. Show the names it returns and stop there — updating the wrong skill silently overwrites a working install, so let the user pick.

## Skill name given

Two commands, in this order:

```bash
npx --yes skills@latest update "$1" --global --yes
```

`update` only works when the skill was originally added from GitHub — an install made from a local path records `source: null` and has no origin to re-download from. When the command reports that the skill is not installed or not tracked, fall back to a fresh install from the marketplace:

```bash
npx --yes skills@latest add massdo/massdo-marketplace \
  --skill "$1" \
  --global \
  --agent codex \
  --agent claude-code \
  --agent cursor \
  --yes
```

This install path is also what makes future `update` calls work, so prefer it over any local-path install.

## Confirm the result

The canonical copy lives in `~/.agents/skills/<skill>/`. Codex and Cursor read that directory directly; Claude Code gets a symlink at `~/.claude/skills/<skill>`. Report the version that landed and, when the user asks where it went, point at those paths rather than guessing.
