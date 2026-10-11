---
name: pause
description: Save only this chat's work context as its latest Nestor transmission. Use only when the user explicitly invokes pause; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Pause

Capture only work from the current conversation. Nestor stores one latest transmission
per authenticated tenant, effective project and exact technical chat identity. A new
pause replaces that chat's capture atomically. Other chats keep their own captures.

The `nestor` skill governs shared MCP procedures and item citations. Change no task
or note. Keep no local handoff storage and install no helper script.

## Identify the plugin version

Pass `{ "version_hash": "105fb8a191ca6d900" }` on every Nestor MCP call.

## Direct invocation and current chat identity

Run only after the user's direct invocation: Claude Code `/nestor:pause [project]`,
Codex `$nestor:pause [project]`, or the equivalent explicit skill action in another client.
Read the whole argument string, including a final `ARGUMENTS: …` line when supplied.
Preserve internal spaces. Blank arguments mean no explicit project.

Obtain the current chat's real technical ID again at every invocation:

- Codex: read the non-empty `CODEX_THREAD_ID` environment value through the client's
  available shell; use the stable source `codex`.
- Claude Code: use the skill substitution `${CLAUDE_SESSION_ID}`; use the stable
  source `claude-code`. A literal, unsubstituted placeholder is unavailable.
- Other clients: use only technical conversation metadata actually exposed by that
  client, with its stable conversation-system namespace. Do not infer availability.

Preserve both strings exactly. A name, model, directory, timestamp, OAuth client ID,
MCP transport session ID, remembered ID or selected transmission's chatId is no
substitute. Changing model or chat name keeps the identity. A new chat uses its own ID.

Without a non-blank real ID, stop before writing and explain the client's identity
limit. Never generate an ID or use another chat's identity. This capture requires
`journal:write`; a read-only connection cannot save it.

## Resolve the effective project

An explicit project takes precedence. Resolve it by exact `get_project`. Only
NOT_FOUND permits `search_project` with that name. Retain a single complete result;
several results or an incomplete page require the user's choice. Announce a retained
name that differs. Report authentication and transport failures as failures.

With a workspace and no explicit project, inspect its Git root, including linked
worktrees and subdirectories. With Git, derive the name from origin's last segment,
without .git, recognizing HTTPS, SSH and SCP forms. With no origin, use the root
directory name. Resolve that name as above. Do not silently switch projects after
a failed lookup. An archived project refuses capture with ARCHIVED.

Without Git and without an explicit project, use `{ "mode": "global" }`, without
attachProjectId. Ask for no project and create none. A client without a workspace
needs no shell or Git inspection. With a resolved project, use its returned ID in
`{ "mode": "project", "projectId": "<resolved id>" }`.

## Capture this conversation

Write the objective, known progress, decisions, blockers and proposed next actions
from this chat. Include only tasks and notes actually worked on here: useful
consultation, diagnosis, decisions or implementation count; a passing mention does not.
An empty task or note array is valid. Unlinked work needs no invented Nestor reference.

Do not search recent modifications, inventory the project or account, or inspect
another conversation. Other chats' activity is not capture evidence. Include no
windowMinutes, sources or legacy kind field.

Reuse verified slugs and observed task statuses held in this conversation. If a
worked item's necessary information is missing, read only that worked item with
get_item, grouping at most five refs and matching known values. A complete held
content/version/ETag pair needs no new read. Never fetch unrelated items. A failed
necessary read stops the capture; do not claim completeness.

The body is a structured object, not Markdown or a JSON string:

```json
{
  "objective": "<known objective or empty string>",
  "progress": "<known progress or empty string>",
  "decisions": [],
  "blockers": [],
  "nextActions": [],
  "tasks": [
    { "slug": "<real task slug>", "summary": "<this chat's work>", "statusAtPause": "in_progress" }
  ],
  "notes": [
    { "slug": "<real note slug>", "summary": "<this chat's work>" }
  ]
}
```

All seven fields are required. Empty objective or progress means unknown. Empty arrays
mean nothing known. Every list string and summary is non-blank. Each slug appears once
across tasks and notes. Task statusAtPause is the observed todo, in_progress, need_review,
completed or cancelled value; do not invent its current state. Summaries have no separate
word or sentence limit. Keep the whole validated compact JSON within 100,000 Unicode
code points, including keys and separators; do not truncate it to force a write.

Only when known, add git with at least one non-blank branch, commit or pullRequest.
Omit unknown Git fields. No Git inspection is required without a workspace.
Record at least one known piece of context. Otherwise explain that nothing needs
capture and write nothing.

Write a separate non-blank preview of at most 200 Unicode code points to distinguish
this chat's objective during discovery. Preserve useful information within the limit.

## Save once and report the confirmed result

Call create_item once with the resolved scope, type transmission, the current chatSource
and chatId, schemaVersion 1, preview and structured body. Send no title, status, tags,
dates, parent, backlog or other task/note field, including explicit nulls.
Send no expectedVersion or expectedEtag. The server supplies the capture time,
canonical ref, reusable scope, ID, slug, version and ETag.

A confirmed save creates or replaces only this exact tenant/project/chat key. Replacing
identical content still increments version and changes ETag, while preserving ID and
slug. No old transmission history is available. Captures do not expire.

Announce only the MCP-confirmed result. Cite its returned slug and description, and
report its technical chat identity and reusable reference. Make no post-success get_item
call. On a failure, report it without local fallback. A lost response leaves an unknown
outcome: claim neither success nor preservation, and do not automatically replay.
