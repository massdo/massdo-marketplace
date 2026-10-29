---
name: next-tasks
description: Show one Nestor project's active Plans, sub-plans and Tasks in their hierarchy, including ready-to-build and building work, for a project named as an argument or inferred from the workspace's Git repository. Use only when the user explicitly invokes next-tasks; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Next Tasks

Show what is moving in one Nestor project: its active Plans, sub-plans and Tasks, with
every active Task visible under its parent. When the complete view is empty, offer its
backlog.

This is a consultation. It creates no project, changes no item and writes nothing. The
`nestor` skill holds the shared journal procedures and the way items are cited; this skill
only decides which project to read and which tasks to show.

## Identify the plugin version

Pass `{ "version_hash": "2cebff959578a0f6c" }` on every Nestor MCP call.

## Invocation

- Claude Code: `/nestor-beta:next-tasks [project]`.
- Codex: `$nestor-beta:next-tasks [project]`.
- Cursor: select the skill, then supply the project name.

Run only when the user invokes this skill directly. The arguments are the text written
after the skill name; depending on the client, they may arrive in a final `ARGUMENTS: …`
line. When the request is phrased in prose instead, read them from the user's message.

**The whole argument string is one project name.** Keep its internal spaces and never split
it into several arguments. An empty or blank string is no argument at all.

## Resolve the project

**An explicit argument is authoritative.** Do not read Git to confirm it or to replace it.
This skill consults tasks; it has no reason to check that the named project matches the
current repository, and the argument is how the user reaches a project from anywhere.

Without an argument, infer the name from the workspace's Git repository:

1. Work from the repository root, not from the current directory — a subdirectory and a
   linked worktree must give the same answer as the root of the reference repository.
2. Read the `origin` remote and keep the last segment of its URL, without a `.git` suffix.
   Recognize the usual HTTPS, SSH and SCP forms, with or without the suffix.
3. With no `origin`, use the name of the repository root directory — never the arbitrary
   directory name of a linked worktree standing in for another project.

When none of this yields a reliable name, ask the user which project to read and stop.
Never silently reuse a project named in an earlier conversation.

### Read the project

Try the exact read first: `get_project` by `name`. Only a failure to match justifies
looking for close names — a transport or authentication error does not mean the project is
absent, so report that and stop instead.

After an exact failure, the rule is the same for an explicit argument and for a name
inferred from Git:

- Call `search_project` with the failed name as `query` and select a project automatically
  only when the search returns a single result **in total**. A partial page never
  establishes that uniqueness. Call it without a `query` to browse the projects.
- With several results, ask the user to choose. Never take the first result for the only
  relevant one — two projects can carry similar names.
- With no result, ask for another name or offer the available projects.

The server owns fuzzy matching: define no distance and no threshold here.

Name the project actually retained whenever it is not the exact name that was asked for,
and announce an archived project before reading it.

## Read the active view

Read the current MCP contracts for `list_items` and `get_item`. Call `list_items` with
`view: "active"` and the resolved project's scope, without filters for roots, status or
type. In particular, do not combine `parentTaskId: null`, `planId: null` and
`parentPlanId: null`: those relations describe different populations.

The mixed view includes Plans and the `todo`, `in_progress`, `need_review`,
`ready_to_build` and `building` Tasks, scheduled or not, with no time bound. It excludes
backlog Tasks, completed and cancelled Tasks, archives, trash and notes. Keep every Plan
the server returns, even without an active Task; do not filter it by progress.

Keep the server's canonical order and pagination; add neither a sort nor a volume limit.
When `hasMore` is true, say results remain and follow its cursor until the view is complete.
A short pagination reference needs only `cursor` and `version_hash`; a legacy cursor
retains the original criteria. Keep relations across pages. If a page cannot be read,
show the available work as partial, never as the whole view or as an empty view.

## Show the hierarchy

After reading the pages, group each item by its explicit relation:

- A Task belongs to a Plan through `planId`.
- A sub-plan belongs to a Plan through `parentPlanId`.
- An ordinary Task's historical parent is `parentTaskId`; this relation creates no Plan.
- An item with no parent relation is autonomous or a root Plan.

Read missing ancestors, recursively, through grouped `get_item` calls of at most five
refs in the same project scope. Send `known: null` when complete content or a matched
pair is absent; otherwise send the held pair. Keep unchanged content and refresh its
project. Mark those ancestors as **context outside the view**, retaining their actual
type and state. Do not expand their other descendants or query their backlog. If an
ancestor cannot be read, keep the child's parent reference explicitly unresolved and
mark the presentation partial; never turn the child into an autonomous entry.

Display each item once in an indented hierarchy. Keep groups in first-encounter order
and preserve the server's relative order among siblings, including across pages; do not
sort locally by priority, date or type. A child returned before its parent still appears
under that parent. In the Skyline example, `scarlet_tiglon (migration du core et de
l’API publique)` appears under `silver_whitefish (refonte de l’architecture)`, with its
reduced core/API scope, rather than as an independent workstream.

For a Task, show its returned status. For a Plan or sub-plan, show its kind, the returned
calculated `progress` (`not_started`, `in_progress`, `blocked` or `completed`) and its
approval separately. A current approval matches `approval.workRevision` to `workRevision`;
if both are held, distinguish it from a recorded older approval. With no approval record,
say none is recorded; with incomplete approval data, leave it unknown. Do not assign a
Task status to a Plan, calculate progress, or infer build eligibility from approval.

Cite every item exactly as the `nestor` skill prescribes, including contextual ancestors.
See [the examples](references/examples.md) for mixed views,
pagination, missing ancestors and a requested backlog.

## Decide whether the view is empty

Use the complete mixed `items` and its consistent `totalCount`, which includes Plans.
If they disagree, report the uncertainty instead of declaring the view empty.
`taskViewCounts` counts Tasks only: zero active Tasks does not mean zero Plans. Never
subtract it from `totalCount` to invent a number of hidden descendants, and never treat
a missing count as zero. A partial read cannot establish emptiness.

Only when the complete active view is actually empty, name the project and offer its
backlog as described below. Any returned Plan or Task ends with that work.

## Offer the backlog

The backlog holds work set aside for later, not work that is moving, so it is never read
unasked. The `active` response already counts it, within the same scope, in
`taskViewCounts.backlog`: decide from that count, without another call.

- Above zero, give the count, subtasks included, and ask whether to show the backlog too,
  then stop and wait for the answer.
- At zero, say the backlog is empty as well and ask nothing: the answer to that question
  is already known.
- Absent, ask the same question without a count rather than read the backlog to find one.

On a yes or a direct backlog request, call `list_items` with `view: "backlog"` in the same
project scope, without root, status or type filters. This view returns Tasks; Plans have
no backlog field. Read their missing ancestors only as context and use the same grouping,
order, pagination, partial-read and citation rules. Do not claim a contextual Plan itself
is in the backlog or subtract Task counters from mixed totals.
