---
description: Interview the user one question at a time, starting from an idea or from an existing Nestor task, until a developer-ready specification emerges, then write it into Nestor as an orchestrator task with self-contained, actionable child tasks.
argument-hint: "<idea… | id-or-slug> [project:<name-or-id>]"
disable-model-invocation: true
---

Raw arguments: `$ARGUMENTS`. Everything that is not `project:<name-or-id>` is the starting point: either the idea to specify, written as prose, or a single token naming an existing Nestor task by id or `color_animal` slug, whose title and body then replace that prose. Empty means nothing was given, and the instructions below tell you to ask for it in one line rather than to guess.

These instructions are inlined from `skills/spec/SKILL.md`, the single source shared with Codex and Cursor. Never copy them back here: a pointer that drifts from its target is worse than no pointer. The leading YAML block only serves skill loading, ignore it.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/spec/SKILL.md"`
