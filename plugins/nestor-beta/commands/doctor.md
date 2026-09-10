---
description: Audit one Nestor project's open tasks against the repository's merged history and close only the ones the code proves are done, after an explicit confirmation.
argument-hint: "[project-ref]"
disable-model-invocation: true
---

Raw arguments: `$ARGUMENTS`. When present, the whole string is one Nestor project ref
(name or id); spaces belong to the name and must be preserved. Empty means the
instructions below list projects and wait for a selection.

Follow the shared skill instructions below. Ignore their YAML frontmatter.

!`cat "${CLAUDE_PLUGIN_ROOT}/skills/doctor/SKILL.md"`
