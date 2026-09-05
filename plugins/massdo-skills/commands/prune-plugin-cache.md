---
description: Delete the stale plugin versions Claude Code leaves in its cache after an update, which make skills and commands appear several times in the picker.
argument-hint: "[nothing to list, or apply to delete]"
---

Argument received: `$1`. Empty means list the orphans without deleting anything; `apply` means delete them.

These instructions are inlined from `skills/prune-plugin-cache/SKILL.md`, the single source shared with Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/prune-plugin-cache/SKILL.md"`
