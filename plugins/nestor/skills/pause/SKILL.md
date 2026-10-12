---
name: pause
description: Save this conversation as its latest Nestor transmission. Run only on the user's explicit pause invocation.
disable-model-invocation: true
---

# Nestor Pause

Invoke `/nestor:pause` or `$nestor:pause` without arguments.
Use the Nestor skill for shared MCP procedures and citations.
Pass `{ "version_hash": "105fb8a191ca6d900" }` on every Nestor MCP call.

## Detect the project and chat

- From the workspace's Git root, infer the project name from origin's final segment
  without .git (HTTPS, SSH or SCP). Subdirectories and worktrees resolve the same
  repository. Without origin, use the reference repository's root directory name.
- Resolve that name with get_project. Only NOT_FOUND permits search_project.
  Retain a single complete result; otherwise ask for a choice. Report other errors.
  Use the returned ID in project scope. Create no project.
- Without Git, use global scope without attachProjectId or a project question.
  A client without a workspace needs no Git inspection.
- Retrieve the real chat ID at each invocation: CODEX_THREAD_ID with source codex,
  substituted `${CLAUDE_SESSION_ID}` with source claude-code, or exposed technical
  conversation metadata with its stable source in another client.
  Preserve both strings exactly. Never use a remembered or selected chat's identity.
  Without a real non-blank ID, including an unsubstituted placeholder, stop before writing.

## Capture and save

Capture only this conversation's work, not recent project activity or other chats.
Use real slugs and observed statuses for tasks and notes actually worked on here.
Read only a worked item whose necessary information is missing, using Nestor's
conditional and grouped reads. A failed necessary read stops capture.

Build the structured body using the MCP schema:

- objective and progress: known text, or empty strings;
- decisions, blockers and nextActions: arrays of known observations;
- tasks: entries with slug, summary and observed statusAtPause;
- notes: entries with slug and summary;
- optional git: only known branch, commit or pullRequest fields.

Empty arrays are valid. Keep slugs unique and summaries non-blank.
If nothing needs capture, write nothing. Add a non-blank preview of at most
200 Unicode code points. Respect the body's 100,000-code-point limit without truncation.

Call create_item once with scope, type transmission, chatSource, chatId,
schemaVersion 1, preview and structured body. Send no task/note fields or preconditions.
This replaces only the current project/chat capture. Change no task or note.

Report the confirmed capture with its citation and reusable ref. Do not read it back.
A lost response means unknown outcome; never replay automatically.
Use no local storage, helper script or legacy workflow-pause note.
