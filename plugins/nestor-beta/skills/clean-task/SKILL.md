---
name: clean-task
description: Clean a specified Nestor task body by removing proven obsolete information, merging true duplicates and condensing prose without losing useful specifications. Use only when the user explicitly invokes clean-task with a task reference; never start from a task, plan, agent or another skill.
argument-hint: "<ref>"
disable-model-invocation: true
---

# Nestor Clean Task

Clean the body of one task while preserving its meaning and ability to stand on its own.
An explicit user invocation authorizes the rewrite directly; do not routinely ask for
approval of a draft. This workflow does not implement the task, clean its children or
modify other items.

## Identify the plugin version

Pass `{ "version_hash": "33e5788bba8455c5" }` on every Nestor MCP call.

## Invocation

- Claude Code: `/nestor-beta:clean-task <ref>`.
- Codex: `$nestor-beta:clean-task <ref>`.
- Cursor: select the skill, then supply the reference.

Read the arguments after the skill name, including a final `ARGUMENTS: …` line when the
client supplies one. Accept exactly one reference: an id, a server-supported id prefix or
an exact slug. With no reference or multiple references, ask only for the single intended
target and stop without mutation. Never infer a target from an earlier task or a plan.

Clean only the body of the specified task; leave its other fields unchanged.

## Decide what can be removed

Start with the body and explicit decisions in the conversation. Consult a referenced
Nestor item or another relevant source only when needed to decide whether a particular
removal is justified; do not start a general repository audit.

- Remove a decision, workaround or point awaiting validation only when a later explicit
  decision or consulted evidence establishes that it is obsolete. Age, completed status
  and past-tense wording are not evidence of obsolescence.
- If evidence is inaccessible, insufficient or contradictory, keep the information and
  report the uncertainty. Never turn an assumption into a verified fact.
- Merge true duplicates without losing a nuance, exception or condition. Information
  repeated in another task is not automatically dispensable: keep this task self-contained
  and preserve useful links.
- Condense explanations, anecdotes and verbose prose only where they carry no rule,
  constraint or rationale needed to understand a decision.
- Preserve scope, exclusions, business rules, acceptance criteria, constraints,
  architecture decisions, useful open questions, applicable commands, snippets and links.
- Keep the original language, typography and valid Markdown, including tables and fenced
  code. Preserve retained commands, identifiers, URLs, values, quotations and markers
  exactly; condensation is not permission to correct them.
- Do not silently resolve business or technical contradictions. Keep unresolved elements,
  report them, and perform the other certain cleanups.

Leave an empty or already clean body unchanged. A second pass over a clean result should
likewise make no change. If the content changes in the meantime, reassess the cleanup
while preserving the new information.

## Report

Briefly describe removals and their evidence, condensations, useful content retained,
and unresolved contradictions or uncertainties. If nothing needs cleaning, say so.
