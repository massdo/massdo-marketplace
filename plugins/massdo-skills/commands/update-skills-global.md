---
description: Update a skill from the massdo marketplace globally, for Codex, Claude Code and Cursor.
argument-hint: "[skill-name]"
allowed-tools: Bash(npx:*)
---

Target skill : `$1`. When `$1` is empty, follow the branch below that covers a missing name.

These instructions are inlined from `skills/update-skills-global/SKILL.md`, the single source shared with Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/update-skills-global/SKILL.md"`
