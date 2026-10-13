---
name: pause
description: Save this conversation as its latest Nestor transmission. Run only on the user's explicit pause invocation.
argument-hint: "[capture focus]"
disable-model-invocation: true
---

# Nestor Pause

Use the Nestor skill for shared MCP procedures and citations.
Pass `{ "version_hash": "133fa51871e394b96" }` on every Nestor MCP call.

## Identify the chat

Use this chat's real technical ID as chatId and preserve it exactly.
Never reuse another chat's ID. If this ID is unavailable, stop before writing.

## Capture and save

Capture only this conversation's work, not recent journal activity.
An argument guides what the capture emphasizes, such as its objective, preview or next actions.
Use real slugs and observed statuses for tasks and notes actually worked on here.
Read only a worked item whose necessary information is missing, using Nestor's
conditional and grouped reads. A failed necessary read stops capture.

Build the structured body using the MCP schema:

- objective and progress: known text, or empty strings;
- decisions, blockers and nextActions: arrays of known observations;
- tasks: entries with slug, summary and observed statusAtPause;
- notes: entries with slug and summary;
- optional git: only known branch, commit or pullRequest fields; omit git when none is known.

Empty arrays are valid. Keep slugs unique and summaries non-blank.
If nothing needs capture, write nothing. Add a preview: a short business summary of
this work, at most 200 Unicode code points. Respect the body's 100,000-code-point limit
without truncation.

Call create_item once with global scope, type transmission, chatId, schemaVersion 1,
preview and structured body. Send no project, task/note fields or preconditions.
This replaces only this chat's current transmission. Change no task or note.

Report the confirmed transmission with its citation and reusable ref. Do not read it back.
A validation rejection writes nothing: correct the reported fields and retry once.
A lost response means unknown outcome; never replay automatically.
Use no local storage, helper script or legacy workflow-pause note.
