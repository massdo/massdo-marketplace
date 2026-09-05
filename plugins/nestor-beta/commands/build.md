---
description: Build a Nestor task end to end into a validated target branch; prod requires explicit confirmation before shipping.
argument-hint: "<id-or-slug> [prod] [target:<branch>]"
---

Raw arguments: `$ARGUMENTS`. The first is a Nestor item id or a `color_animal` slug. After it, `prod` and `target:<branch>` are optional named arguments and may appear in either order. Without a target, `prod` requests `main`; without `prod`, fetch the remote branches and ask the user to choose. Empty means no task target was given, and the instructions below tell you to stop right there.

These instructions are inlined from `skills/build/SKILL.md`, the single source shared with Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md"`
