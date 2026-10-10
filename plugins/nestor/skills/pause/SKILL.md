---
name: pause
description: Save a project's work context and summaries in a Nestor handoff note for a later conversation. Use only when the user explicitly invokes pause; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Pause

Capture the context of interrupted work in one project. The agent writes the summaries;
Nestor stores them. The handoff describes the state at capture time and lets `resume`
restore it without reading the linked tasks or notes.

The `nestor` skill governs shared MCP procedures, conditional reads and item citations.
This workflow creates one note; it changes no existing task or note and keeps no local
handoff storage.

## Identify the plugin version

Pass `{ "version_hash": "1bc829a8788f8b6f3" }` on every Nestor MCP call.

## Invocation and project

- Claude Code: `/nestor:pause [project]`.
- Codex: `$nestor:pause [project]`.
- Cursor: select the skill, then supply the project name.

Run only after a direct invocation by the user. Read the arguments after the skill name,
including a final `ARGUMENTS: …` line when the client supplies one. The whole argument
string is one project name: preserve internal spaces. Blank arguments mean no project
was supplied.

An explicit project takes precedence over the workspace; do not read Git to replace it.
Otherwise resolve it from the workspace:

1. Find the workspace's Git root; a subdirectory or linked worktree must resolve as its
   root does.
2. Read `origin` and take the last URL segment without `.git`, recognizing HTTPS, SSH
   and SCP forms. With no `origin`, take the root directory's name.
3. If no reliable name results, ask for a project and stop before any mutation.
4. Read the exact name with `get_project`. Only a not-found result permits
   `search_project` with that name as `query`; a transport or authentication error is
   reported as a failure. A single result in total may be retained; several results or
   an incomplete page require clarification. Announce a retained name that differs.
5. Stop on an archived project: it cannot accept the handoff. Never create a project
   automatically or fall back to all projects.

Use `{ "mode": "project", "projectId": "<resolved id>" }` for every scoped call below.

## Select the work to capture

Read UTC with `date -u` immediately after resolving the project. Hold that instant T;
do not substitute a guessed time or the conversation's date. Capture at whole-second
precision and format `capturedAt` with `.000Z`. Calculate the lower bound from that
same instant, including across midnight:

```sh
capturedSeconds=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
# macOS
date -u -j -v-60M -f '%Y-%m-%dT%H:%M:%SZ' "$capturedSeconds" '+%Y-%m-%dT%H:%M:%S.000Z'
# Linux: use this alternative instead of the macOS command
date -u -d "$capturedSeconds - 60 minutes" '+%Y-%m-%dT%H:%M:%S.000Z'
```

Run the alternative appropriate to the host. If capture or calculation fails or yields
an unreadable instant, explain the failure and stop without creating a note.

Start exactly two filtered `search_items` searches in the resolved project:

| Search | Arguments |
| --- | --- |
| Tasks | `filters: { "types": ["task"], "dateFrom": { "instant": "<T minus 60 minutes>" } }`, `limit: 50` |
| Notes | The same lower bound and limit, `filters.types: ["note"]`, `includeTags: true` |

Omit `query` and `dateTo`. Without text the search is deterministic, the date filter
selects modification time, and pagination uses cursors. The lower bound is inclusive.
Follow each search's cursor to its last page, using the short pagination request
`{ "cursor": "<returned cursor>", "version_hash": "1bc829a8788f8b6f3" }`. Report
`hasMore` while pages remain; a missing page prevents a complete handoff.

Keep modifications in the interval T minus 60 minutes through T; exclude results
modified after T from the `modified` source. The searches include subtasks and backlog
tasks, and exclude archives, trash, completed and cancelled tasks. Do not add a roots-only
filter or inventory the backlog separately. Exclude notes tagged `workflow-pause`.
Never use `list_events` or `list_items` for this selection.

Add tasks and notes actually worked on in this conversation, even when their Nestor
modification is older. Useful consultation, diagnosis, decisions and implementation
count as work; a passing mention does not. Invent no Nestor reference for unlinked work.
Verify every worked item absent from the searches with `get_item`, in groups of at most
five references in `ref`, with the corresponding `known` array. Send the matched
version/ETag pair when the necessary content is held; otherwise send null. On
`unchanged: true`, retain the held content and pair and refresh the project name.
Inspect each grouped result, including its own `error`.

Keep only items belonging to the resolved project: tasks in `todo`, `in_progress` or
`need_review`, and ordinary notes. Exclude archived or trashed items and `workflow-pause`
notes from both sources. Deduplicate by returned identity, including subtasks; combine
the proven sources instead of creating a second entry.

For each search result not worked on in the conversation, read its body with `get_item`
before summarizing it. A search excerpt is insufficient evidence of progress. Group
up to five references, using `known: null` per reference unless its necessary content
and pair are already held. Recheck project, type, visibility and task status from the
full or held unchanged result. Use `modified` only for a proven modification within
the captured window; `conversation` only for proven work in this conversation.

If no task or note survives but the conversation has an objective, decision, blocker
or next action worth keeping, still create the handoff with `tasks: []` and `notes: []`.
Without any context worth keeping, explain that result and create nothing. If a necessary
read fails or remains incomplete, report it and stop before creating a handoff that
would imply a complete capture. Do not change any existing item's content, status,
dates or tags.

## Write and store one self-contained handoff

Write each selected task's and note's summary yourself: one or two sentences, at most
50 words, covering its subject, known progress and useful point of continuation. Make
unknown information explicit. Write the overall objective, progress, decisions,
blockers and proposed next actions in a useful order, without inventing any of them.

The title is exactly `Pause — <capturedAt>`, with T in UTC ISO 8601 with milliseconds.
The body contains one JSON code block, with no duplicate summary section:

```json
{
  "kind": "nestor.pause",
  "schemaVersion": 1,
  "projectId": "<id returned by Nestor>",
  "capturedAt": "2026-10-10T08:00:00.000Z",
  "windowMinutes": 60,
  "objective": "<work objective>",
  "progress": "<known overall progress>",
  "decisions": [],
  "blockers": [],
  "nextActions": [],
  "tasks": [
    {
      "slug": "<slug returned by Nestor>",
      "summary": "<agent-written summary>",
      "statusAtPause": "in_progress",
      "sources": ["modified", "conversation"]
    }
  ],
  "notes": [
    {
      "slug": "<slug returned by Nestor>",
      "summary": "<agent-written summary>",
      "sources": ["modified"]
    }
  ]
}
```

`objective`, `progress` and each summary are strings. `decisions`, `blockers` and
`nextActions` are arrays of strings; empty arrays mean nothing known to record.
`tasks: []` and `notes: []` are valid. Each slug appears once, exactly as returned by
Nestor. A task's `statusAtPause` is `todo`, `in_progress` or `need_review`.
`sources` contains `modified`, `conversation` or both, matching the selection evidence.

Only for code work with known Git observations, add an optional `git` object with any
known `branch`, `commit` and `pullRequest` strings. Omit unknown fields. Copy no full
task or note bodies, identifiers, versions or ETags into the handoff; `resume` needs
only the slugs and summaries. The note's own version and ETag are assigned by Nestor.

Call `create_item` once in the resolved project, with `type: "note"`, this title and
body, and `tagNames: ["workflow-pause"]`. This is an ordinary tag, not a reserved
system marker. Each pause creates a distinct note; do not rewrite or archive previous
handoffs. There is no automatic expiration, so a handoff remains usable after eight
hours or longer. `resume` archives the note it consumes; neither skill deletes it.

Announce only an MCP-confirmed creation and cite the returned note using Nestor's
slug-and-description format. An MCP failure produces no invented result or local
fallback. If the creation response is lost, report an unknown outcome and do not
automatically replay the call. Reuse a confirmed mutation's returned pair directly
when needed; make no post-success `get_item` verification call.
