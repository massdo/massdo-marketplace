---
description: Write every reply articulately, in full sentences that are neither telegraphic nor padded, and in the language the user writes in. Pass a number to cap every reply at that many words. Stays on until /massdo-skills:articulate reset.
argument-hint: "[word cap, or reset]"
disable-model-invocation: true
---

Arguments received: `$ARGUMENTS`. Empty turns the style on with no cap, a number caps every reply at that many words, `reset` drops the style.

These instructions are inlined from `skills/articulate/SKILL.md`, the single source shared with Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/articulate/SKILL.md"`
