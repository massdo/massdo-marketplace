---
name: resume
description: Restore a Nestor transmission without mutation or starting work. Run only on the user's explicit resume invocation.
argument-hint: "[list | slug]"
disable-model-invocation: true
---

# Nestor Resume

Use the Nestor skill for shared MCP procedures, conditional reads and citations.
Pass `{ "version_hash": "10d15cff38fabeb39" }` on every Nestor MCP call.
This workflow is read-only. Start no work and invoke no other skill.

## Find the transmission

With `list`, go directly to the list.

Another argument names a transmission: call get_item with it as ref, global scope
and known; omit type and chatId. A transmission restores directly. NOT_FOUND,
AMBIGUOUS or another item type shows the list. Other errors stop the workflow.

Without an argument, call get_item with global scope, type transmission, this chat's real
technical ID as chatId, and known; omit ref. Preserve the ID exactly and follow
Nestor's conditional-read rules. A successful read restores directly.
NOT_FOUND, or an unavailable chat ID, shows the list. Other errors stop the workflow.

## List and select

Call list_items with view transmissions, projection compact and global scope.
Keep the returned order, newest first. Show one transmission per line: its citation,
with the preview as description, then its relative capture date in the
conversation's language. For example:

- `azd_azd (business summary)` - yesterday 20:23
- `blue_charcoal (business summary)` - 3 days ago

Capture dates are UTC. Convert them to local time and compare them with the current
local time; get the current time and time zone first when they are unknown. Without
them, show the UTC date and time and no relative label.

Report hasMore. Read no body. An empty list means no transmission is saved.

Wait for an explicit choice, even with one candidate. Then read exactly that
transmission with get_item, its complete returned ref, global scope and known.
Omit type and chatId with ref. Never adopt the selected transmission's chatId.
A failed read selects no alternative.

## Restore

Require type transmission and schemaVersion 1. Restore objective, progress, decisions,
blockers, nextActions and all saved task/note summaries from its structured body.
Show the capture date, converted the same way, and the version. Saved statuses and
Git fields are observations, not current state. Account for explicit newer facts
already in this conversation.

Read no linked item. Change no transmission, task or note; repeated resume remains possible.
Ignore legacy workflow-pause notes. Use no local storage or helper script.
