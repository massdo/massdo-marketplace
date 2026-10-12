---
name: resume
description: Restore a Nestor transmission without mutation or starting work. Run only on the user's explicit resume invocation.
argument-hint: "[list]"
disable-model-invocation: true
---

# Nestor Resume

Invoke `/nestor:resume` or `$nestor:resume`; the only optional argument is `list`.
Use the Nestor skill for shared MCP procedures, conditional reads and citations.
Pass `{ "version_hash": "105fb8a191ca6d900" }` on every Nestor MCP call.
This workflow is read-only. Start no work and invoke no other skill.

## Find the transmission

With `list`, skip project and chat detection. Discover in global scope, including
captures outside projects and in archived projects.

Otherwise:

- Infer the project from origin's final segment without .git (HTTPS, SSH or SCP),
  using the workspace's Git root. Subdirectories and worktrees resolve the same
  repository. Without origin, use the reference repository's root directory name.
- Resolve with get_project. Only NOT_FOUND permits search_project. Retain a single
  complete result; otherwise ask for a choice. Report other errors. Create no project.
  Use the returned ID in project scope; without Git, use global scope.
  A client without a workspace needs no Git inspection or project question.
- Retrieve the real chat ID again: CODEX_THREAD_ID with source codex,
  substituted `${CLAUDE_SESSION_ID}` with source claude-code, or exposed technical
  conversation metadata with its stable source in another client.
  Preserve the exact strings. Never adopt a selected transmission's chat identity.
- With an accessible identity, call get_item with scope, type transmission,
  chatSource, chatId and known; omit ref. Follow Nestor's conditional-read rules.
  A successful read restores directly.
- In a project, NOT_FOUND or an unavailable chat ID starts project discovery.
  Outside projects, NOT_FOUND means no capture for this chat; an unavailable ID
  requires `resume list`. Other errors stop the workflow.

## Discover and select

Call list_items with view transmissions, projection compact and the chosen scope.
Show returned ref or slug, capturedAt, preview and project; identify captures outside
projects. Follow returned cursors and report hasMore. Read no candidate body.

Wait for an explicit choice, even with one candidate. Then read exactly that capture
with get_item, its complete returned ref and exact scope, plus known.
Omit type and chat identity with ref. Never replace complete selectors with display IDs.
An empty complete list means no captures in that scope. A failed read selects no alternative.

## Restore

Require type transmission and schemaVersion 1. Restore objective, progress, decisions,
blockers, nextActions and all saved task/note summaries from its structured body.
Show project, capture date and version. Saved statuses and Git fields are observations,
not current state. Account for explicit newer facts already in this conversation.

Read no linked item. Change no capture, task or note; repeated resume remains possible.
Ignore legacy workflow-pause notes. Use no local storage or helper script.
