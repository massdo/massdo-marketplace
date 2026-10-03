---
name: doctor
description: Audit a Nestor project's open tasks against the merged pull requests whose footer references them and propose evidence-backed closures for user approval. Use only on an explicit doctor request; the project is named as an argument or inferred from the workspace's Git repository.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Doctor

Find tasks whose implementation has been merged into the repository but which remain open
in Nestor. Propose closing them and wait for the user's approval.

Run this workflow only on the user's explicit doctor request. Never start it on your own
initiative.

Use the Nestor skill for journal operations and the MCP catalogue for tool contracts.

## Identify the plugin version

Pass `{ "version_hash": "277cfad66a8f3745e" }` on every Nestor MCP call.

## 1. Select the project and tasks

`/nestor-beta:doctor [project]` — Codex: `$nestor-beta:doctor [project]`; Cursor: select
the skill, then supply the project name.

The arguments are the text written after the skill name at invocation; depending on the
client, they may arrive in a final `ARGUMENTS: …` line. For an equivalent request in natural
language, read them from the user's message. The whole argument string is one project name:
never split it, and keep its internal spaces as part of the name. An empty or blank string
is no argument at all.

**An explicit name is authoritative.** Do not read Git to confirm it or to replace it, and
do not require it to match the repository being audited: doctor consults a project's tasks,
and the argument is how the user reaches a project from anywhere. Even a name that looks
like an id is read with `name`. The Git reads below serve the audit of deliveries after the
selection; the argument never names another repository path.

Without an argument, infer the name from the workspace's Git repository:

1. Work from the repository root, not from the current directory — a subdirectory and a
   linked worktree must give the same answer as the root of the reference repository.
2. Read the `origin` remote and keep the last segment of its URL, without a `.git` suffix.
   Recognize the usual HTTPS, SSH and SCP forms, with or without the suffix.
3. With no `origin`, use the name of the repository root directory — never the arbitrary
   directory name of a linked worktree standing in for another project.

When none of this yields a reliable name, ask the user which project to audit and stop.
Never silently reuse a project named in an earlier conversation.

### Resolve the project

Try the exact read first: `get_project` by `name`. Only a failure to match justifies
looking for close names — a transport or authentication error does not mean the project is
absent, so report that and stop instead of searching.

After an exact failure, the rule is the same for an explicit argument and for a name
inferred from Git:

- Call `search_project` with the failed name as `query` and select a project automatically
  only when the search returns a single result **in total**. A partial page never
  establishes that uniqueness. Call it without a `query` to browse the projects.
- With several results, ask the user to choose. Never take the first result for the only
  relevant one — two projects can carry similar names.
- With no result, ask for another name or offer the available projects.

The server owns fuzzy matching: define no distance and no threshold here. This selection
creates no project.

Name the project actually retained whenever it is not the exact name that was asked for,
and announce an archived project before reading its tasks. Use the id Nestor returns for
the project scope of every later call.

Read all project tasks in `todo`, `in_progress` and `need_review`, including their full
descriptions and completion criteria. Exclude backlog, archived and already-closed tasks.
If no tasks qualify, report that and stop.

## 2. Find merged implementation evidence

Identify the repository's integration branch and refresh its remote history. If the branch
or freshness cannot be established, report the limitation and stop before proposing closures.
Pin the integration commit and inspect its tree. Unmerged branches and local changes do
not count as delivered work.

A merged pull request references the tasks it contributes to in its footer and nowhere
else: one visible line, the last of its description.

```
nestor tasks: brown_turtle, gray_xerinae, copper_manatee
```

These are the tasks' slugs, exactly as Nestor returns them, never ids, separated by a comma
and a space.

Read the description of every pull request merged since the earliest creation date among
the audited tasks; omit this bound if a creation date is missing. Extract slugs from that
footer only, never from a title, the rest of a description, a branch name or a commit
message. Compare them with the task slugs exactly: no substring match, and no semantic
matching between a task and a pull request that resembles it. A missing or invalid footer
references no task.

Confirm that each referencing PR delivered its changes into the pinned integration history.
If PR descriptions cannot be read, report that limitation and propose no closure; never fall
back to commits.

## 3. Check completion

Propose closure only when both conditions are verified:

- The footer of a merged PR, delivered into the pinned history, lists the task's exact slug.
- The implementation in the pinned tree satisfies all completion criteria in the task.
  Inspect the relevant code and diffs; a merged PR and a valid footer alone are
  insufficient, since a footer may reference a partial contribution.

Leave uncertain or partially implemented tasks open for user review. This includes tasks
with vague criteria or requirements that cannot be verified from the repository.

For parent tasks, check all children, including those outside the audit's status selection.
Propose closing a parent only when every child is closed. Incomplete child information
requires user review. Put `need_review` tasks in the user-review group even if their
implementation appears complete.

## 4. Report and request approval

Present three groups:

- **Proposed closures:** task reference, title, supporting PRs and code evidence.
- **Needs user review:** evidence found and the missing or uncertain criteria.
- **No evidence:** count of tasks for which no footer reference or implementation evidence
  was found.

Give every audited task a delivery confidence score from 0 to 100: the probability that it
is delivered in the pinned integration history and meets all its completion criteria. One
scale serves the three groups. The score does not measure how certain the grouping is, and
it never changes a task's group, what an approval covers, or which tasks close. A
`need_review` task stays in **Needs user review** even when its evidence is complete and it
scores 95%.

Calibrate the score on two indicative anchors rather than a rigid formula:

- 90% or more: the footer of a merged PR references the task, and the pinned tree satisfies
  all its completion criteria.
- 5% at most: no footer reference and no implementation evidence was found.

Between them, set the score by judgment.

Start each task line in **Proposed closures** and **Needs user review** with its integer
percentage, followed by ` - ` and the task's citation. **No evidence** stays a count,
prefixed with the highest score among its tasks:

```
Needs user review
95% - coffee_wildfowl (project search)
20% - copper_manatee (OpenAI publication)

5% - No evidence (18; highest score)
```

Ask the user to approve the proposed closures or select individual tasks. Wait for their
answer before making changes. A general approval applies only to the proposed-closure
group; a task in the review group requires explicit selection.

## 5. Close approved tasks

Mark only the approved tasks as completed. If a task's scope or completion criteria changed
since the audit, return it to review before closing it.

Report confirmed closures, failures and any unknown outcomes. Leave all other tasks unchanged.

Do not edit repository files, create branches or commit as part of this workflow.
