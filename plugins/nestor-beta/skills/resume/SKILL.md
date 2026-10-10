---
name: resume
description: Restore a project's saved Nestor handoff and archive that note, without starting work. Use only when the user explicitly invokes resume; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Resume

Restore the context and proposed next actions saved by `pause`. Read only the selected
handoff note's body, prepare the response, then archive that note automatically.
Do not start work or invoke another skill.

The `nestor` skill governs shared MCP procedures, conditional reads, optimistic
mutations and item citations. Its journal MCP server is provided by the nestor plugin.

## Identify the plugin version

Pass `{ "version_hash": "2a2cc476ca4c165c2" }` on every Nestor MCP call.

## Invocation and project

- Claude Code: `/nestor-beta:resume [project]`.
- Codex: `$nestor-beta:resume [project]`.
- Cursor: select the skill, then supply the project name.

Run only after a direct user invocation. Read arguments after the skill name, including
a final `ARGUMENTS: …` line when supplied by the client. The whole argument string is
one project name: preserve internal spaces. Blank arguments mean no explicit project.

An explicit project takes precedence over the workspace; do not read Git to replace it.
Otherwise resolve it from the workspace:

1. Find the workspace's Git root, including from a subdirectory or linked worktree.
2. Take the last segment of `origin` without `.git`, recognizing HTTPS, SSH and SCP
   forms. With no `origin`, take the root directory's name.
3. If no reliable name results, ask for the project and stop before any mutation.
4. Read the exact name with `get_project`. Only a not-found result permits
   `search_project` with that name as `query`. Report transport or authentication
   failures instead of treating them as an absent project. Retain a single result in
   total; several results or an incomplete page require clarification. Announce a
   retained name that differs.
5. Stop on an archived project: it cannot accept the required archive mutation. Never
   create a project automatically or fall back to all projects.

Use `{ "mode": "project", "projectId": "<resolved id>" }` for every scoped call below.

## Reading budget

Discovery reads only handoff metadata. In the normal path, one `get_item` reads the
selected handoff; a conditional unchanged response reuses its held content.
Never read a linked task or note, resolve its slug, verify its current status, compare
its versions or consult its history. Do not inventory tasks or search their contents.
Do not use snapshots or `list_events` to enrich the response. These limits also apply
to error and conflict handling: an inaccessible linked slug still has its saved summary.

## Select and validate one handoff

Call `list_items` in the resolved project's scope with `view: "notes"` and
`filters: { "tagNames": ["workflow-pause"] }`. Use the server's normal compact
projection, not full bodies. Only non-archived, non-trashed notes are candidates.

Parse the exact structured titles `Pause — <capturedAt>`, where `capturedAt` is a
valid UTC ISO 8601 instant with milliseconds. Traverse all metadata pages needed to
establish the latest capture, following each returned cursor with `version_hash`.
Never present a partial discovery as exhaustive. Choose the greatest title timestamp,
not the most recently modified note: changing an old body does not make it the latest
capture. Apply no recency cutoff; a note eight hours old or older remains eligible.
Report incompatible titles without reading their bodies. Read no unselected body.

Read the chosen note with `get_item`, using its returned reference in `ref` and the
resolved project scope. Pass `known: null` when its necessary content or matched pair
is absent; otherwise pass the held `{ "version": ..., "etag": ... }`. With
`unchanged: true`, keep that content and pair and refresh the project name. Preserve
the note's matched pair for archiving, with no preventive read before `update_item`.

Check that the result is an available note of the resolved project, still tagged
`workflow-pause`, and that its body contains one JSON block satisfying this contract:

| Field | Required value or type |
| --- | --- |
| `kind` | `"nestor-beta.pause"` |
| `schemaVersion` | `1` |
| `projectId` | The resolved project's returned id |
| `capturedAt` | Valid UTC ISO 8601 instant with milliseconds, identical to the title |
| `windowMinutes` | `60` |
| `objective`, `progress` | Strings |
| `decisions`, `blockers`, `nextActions` | Arrays of strings; empty is valid |
| `tasks` | Array of `slug`, `summary`, `statusAtPause`, `sources`; empty is valid |
| `notes` | Array of `slug`, `summary`, `sources`; empty is valid |
| `git` | Optional object of known `branch`, `commit`, `pullRequest` strings |

Each linked entry has a non-empty slug and an agent-written summary of one or two
sentences, at most 50 words. Slugs are unique within the saved entries.
`statusAtPause` must be `todo`, `in_progress` or `need_review`. Each `sources` array
contains `modified`, `conversation` or both, without duplicates. The handoff needs
no linked bodies, ids, versions or ETags. Do not fetch missing data from linked items.
If the selected note is invalid or incompatible, explain the failure and leave it
unarchived; do not silently consume an older note instead.

## Prepare the response, then archive

Prepare the entire response from the validated handoff and explicit facts already in
this conversation. State the project and capture time, objective and known progress.
Restore every linked task and note with its saved summary, citing each in one code
span containing its slug and a short description, as Nestor requires. Include known
decisions, blockers and proposed next actions without repeating the summaries.
Empty `tasks` and `notes` mean the context alone is restored. Empty `nextActions`
means none were recorded; invent no work to execute. Git details remain observations
from the pause.

Explain that saved information dates from `capturedAt` and does not verify current
task or note state. When explicit conversation facts show progress since the pause,
use them: an action already completed must not be proposed again. A newer explicit
decision takes precedence over an older contradictory one; state the visible difference.
This reconciliation adds no MCP reads and changes neither the handoff body nor tasks.

Only once validation and response preparation are complete, archive the selected note
with `update_item`, `operation: "patch"`, `patch: { "archived": true }`. Use the
note's held pair directly as `expectedVersion` and `expectedEtag`; archive is the only
patch field. Do not ask for an extra confirmation, make a preventive read or perform
a post-success read. Change no other note or task. Archived handoffs remain in Nestor;
never delete them.

Present the prepared context and the confirmed archive result. Do not start the next
actions automatically or claim that response delivery is guaranteed before a transport
interruption.

For an optimistic conflict, discard the refused pair and use `details.current` when
present; it supplies the current selected note and its matched pair. Only when that
field is absent may one conditional `get_item` of this same note resolve the conflict.
Never read a linked task or note. If already archived, report that state with no
unnecessary mutation. If trashed, moved, untagged or invalid, stop mutations and explain
the change. If content changed, revalidate it and fully adapt the response before one
retry with the new pair. Never mix a version and ETag from different responses or
replay the old patch blindly. A second conflict ends the archive attempt.

## Errors and uncertain outcomes

- An unknown or ambiguous project requires clarification before mutation.
- A discovery or note-read MCP failure is reported without invented data or local
  fallback. Missing metadata pages prevent a definitive selection.
- With no available handoff, say so. Do not consult another project, search archives
  or automatically reuse an archived note. A second resume with no other note has the
  same empty result.
- An incompatible selected note is reported and left unarchived. Do not use linked
  items to repair its missing information.
- If archiving fails, present the already prepared context and say that archiving was
  not confirmed. A persistent conflict after the single adapted retry stops mutations.
- A lost archive response means the outcome is unknown. Do not claim success, perform
  a verification read or automatically replay the mutation.
- Missing or inaccessible linked items retain their recorded summaries or explicit
  unknowns. None of these paths authorizes reading their content or history, starting
  work, or changing anything beyond the selected note's archive visibility.
