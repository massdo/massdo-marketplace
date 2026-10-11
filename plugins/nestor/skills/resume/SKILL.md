---
name: resume
description: Restore this chat's latest Nestor transmission, or explicitly select one from compact discovery, without mutation or starting work. Use only when the user explicitly invokes resume; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project | list]"
disable-model-invocation: true
---

# Nestor Resume

Restore the selected transmission's saved context and proposed next actions. This
workflow is read-only. Do not archive, delete, mark consumed, change versions, start
work or invoke another skill. Repeated resume may restore the same capture.

The `nestor` skill governs shared MCP procedures, conditional reads and item citations.
Read no linked task or note, its current status, version, content or history.

## Identify the plugin version

Pass `{ "version_hash": "105fb8a191ca6d900" }` on every Nestor MCP call.

## Invocation and mode

Run only after the user's direct invocation: Claude Code `/nestor:resume [project | list]`,
Codex `$nestor:resume [project | list]`, or another client's explicit skill action.
Read the whole argument string, including a final `ARGUMENTS: …` line when supplied.
Preserve internal spaces. The exact argument `list` selects global compact discovery;
it is not a project name. Blank arguments mean no explicit project.

With list, use `scope: { "mode": "global" }` and skip workspace, project and chat-identity
lookup. Discover every available transmission of the authenticated tenant, including
floating captures and captures in archived projects. Read no body before a choice.

## Ordinary resume: project and current identity

An explicit project takes precedence. Resolve it with exact get_project. Only NOT_FOUND
permits search_project with that name. Retain a single complete result; ambiguous or
incomplete results require the user's choice. Announce a differing retained name.
Report authentication and transport failures. Do not create a project automatically.

With a workspace and no explicit project, inspect its Git root, including linked
worktrees and subdirectories. If Git exists, derive the project from origin's final
segment without .git, recognizing HTTPS, SSH and SCP forms. With no origin use the
root directory name. Resolve it as above. Never fall back to another project.
Archived projects remain readable; archive does not consume transmissions.

Without Git and without an explicit project, use global scope outside projects.
A client without a workspace needs no shell or Git inspection and no project choice.

Obtain the current chat's real technical identity again, without relying on a remembered
context value:

- Codex: read non-empty CODEX_THREAD_ID from the available environment; chatSource is codex.
- Claude Code: use the substituted `${CLAUDE_SESSION_ID}`; chatSource is claude-code.
  An unsubstituted placeholder is unavailable.
- Other clients: use only technical conversation metadata actually exposed, with a
  stable conversation-system namespace. Do not infer access.

Preserve chatSource and chatId exactly. Names, models, directories, timestamps, MCP
transport sessions and OAuth client IDs cannot replace them. Selecting another chat's
transmission never adopts its identity. A later pause still saves under the current
chat's own ID.

With an accessible identity, call get_item using the resolved scope, type transmission,
chatSource, chatId and known; omit ref. In a project, this selects only that project's
exact key. Global identity lookup selects only a capture outside projects, never the
same identity in another project.

Pass known null without complete held content and its matched pair; otherwise pass
that content's version and ETag. With unchanged true, keep that content and pair and
refresh the project name. A full response replaces the held content and pair.

A successful direct read goes straight to restoration. Only NOT_FOUND in a resolved
project starts compact discovery of that project. Without an accessible identity,
a resolved project also starts that discovery. A storage, authentication, transport
or validation error is a failure, never an absent capture and never a fallback.

Outside projects, an identified chat with NOT_FOUND reports no capture for this chat.
Outside projects without an accessible identity, explain the direct-resume limitation
and indicate resume list. Do not claim no transmissions exist.

## Compact discovery and explicit choice

Call list_items with view transmissions, projection compact and the selected scope.
Use no task, tag, date or backlog filters. Do not call search_items, list_events or
get_item for candidates. One list page supplies all its previews directly.

Present each returned ref or slug, capturedAt, preview and project. Mark project null
explicitly as outside projects. In project discovery, the project can be named once.
Keep each entry's canonical complete ref, scope and scope.projectId for selection;
display IDs are not substitute selectors. Several captures of the same project are valid.

Follow pages with only the returned cursor and version_hash. Signal an incomplete
list while hasMore is true. INVALID_CURSOR after a concurrent capture means discovery
is incomplete; restart only compact discovery when useful. Never read bodies to
repair an incomplete list.

Await an explicit user choice even with one candidate. Do not choose by date, preview,
workspace or another chat's identity. An empty complete list reports no available
transmissions in that discovery scope. A failed list reports the failure.

After the choice, read exactly one selected transmission with get_item, its complete
ref and exact returned scope. Do not send type or chat identity with ref. Use known null
without complete held content and its matched pair; otherwise send that pair.
Read no other candidate and no linked item. Failure or disappearance does not permit
selecting an alternative. If capture changed after discovery, use the full version
and capturedAt returned by this read and identify the newer capture.

## Validate and restore without mutation

Validate the selected result as type transmission, schemaVersion 1, with the structured
objective, progress, decisions, blockers, nextActions, tasks and notes contract.
Only git is optional. Required strings and observations retain their saved meanings;
empty strings and arrays mean unknown or nothing recorded. A malformed stored capture
or unsupported schema is a failure. Do not repair it or fetch linked data.

Prepare the response only from this saved body and explicit facts already in this
conversation. State the project or absence of project, capture date and version.
Restore the objective, progress, all saved task and note summaries, decisions, blockers
and proposed next actions. Cite real saved slugs with descriptions as Nestor requires.
Git fields remain capture-time observations. Saved statuses and summaries do not
verify the current task or note state. Empty nextActions authorizes no invented work.

Account for explicit newer conversation progress without extra reads. Do not propose
an action already completed here. An explicit newer decision supersedes a contradictory
saved decision; explain the visible difference.

Return the prepared context. Leave every transmission available, including the chosen
capture and all unselected captures. Issue no update_item or other mutation. A capture
saved after this read remains available for the next resume.

Ignore legacy workflow-pause notes and nestor.pause bodies. Do not discover, read,
archive, migrate or use them as fallback transmissions. Do not install external scripts,
keep local storage or invoke another skill. Errors and interrupted response delivery
never authorize mutation, linked-item reads or starting work.
