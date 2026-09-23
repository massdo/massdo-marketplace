---
name: next-tasks
description: List the active tasks of one Nestor project — todo, in progress and awaiting review — for a project named as an argument or inferred from the workspace's Git repository. Use only when the user explicitly invokes next-tasks; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Next Tasks

Show what is moving in one Nestor project: the tasks of its `active` view. When nothing
is, offer its backlog.

This is a consultation. It creates no project, changes no item and writes nothing. The
`nestor` skill holds the shared journal procedures and the way items are cited; this skill
only decides which project to read and which tasks to show.

## Identify the plugin version

Pass `{ "version_hash": "ccfd4427861104bb" }` on every Nestor MCP call.

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
   linked worktree must give the same answer as the root.
2. Read the `origin` remote and keep the last segment of its URL, without a `.git` suffix.
   Recognize the usual HTTPS, SSH and SCP forms.
3. With no `origin`, use the name of the repository root directory.

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

## Read the active tasks

Call `list_items` with `view: "active"` in the resolved project's scope.

That view holds the `todo`, `in_progress` and `need_review` tasks, scheduled or not, with
no time bound. It already leaves out the backlog, completed and cancelled tasks, archives,
the trash and every note. Add no further filter — in particular, do not restrict the read
to root tasks, since a subtask is active work like any other.

**Keep the server's order**: descending priority, then ascending schedule, then descending
modification, with the server breaking ties. Never re-sort the pages here.

**Keep the server's pagination.** Add no volume limit of your own. When a response carries
`hasMore`, say that results remain; a partial page is never presented as the whole view.

When the view is empty, say so, name the project that was read, then offer the backlog as
described below.

Cite the items exactly as the `nestor` skill prescribes. Invent no layout, no grouping and
no table of your own: one citation form across every skill is what makes an item reference
recognizable from one answer to the next.

## Offer the backlog

Only an empty `active` view leads here. A view with tasks, even a partial page of them,
ends with those tasks.

The backlog holds work set aside for later, not work that is moving, so it is never read
unasked. The `active` response already counts it, within the same scope, in
`taskViewCounts.backlog`: decide from that count, without another call.

- Above zero, give the count and ask whether to show the backlog too, then stop and wait
  for the answer.
- At zero, say the backlog is empty as well and ask nothing: the answer to that question
  is already known.
- Absent, ask the same question without a count rather than read the backlog to find one.

On a yes, call `list_items` with `view: "backlog"` in the same project scope and show it
under the rules of the active view: no further filter, the server's order and pagination,
`hasMore` reported, the same citation form.
