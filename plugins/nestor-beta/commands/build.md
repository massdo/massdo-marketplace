---
description: Build a specified Nestor task end to end into a validated target branch, delegate its implementation, audit every commit, close the task, and optionally ship with prod after explicit confirmation.
argument-hint: "<id-or-slug> [prod] [target:<branch>]"
---

Raw arguments: `$ARGUMENTS`. Treat them as the build request. An empty argument string ends
the turn immediately, as the instructions below require.

These instructions are inlined from `skills/build/SKILL.md`, the single source shared with
Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse
than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md"`
