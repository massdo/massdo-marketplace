---
name: doctor
description: Audit a Nestor project's open tasks against merged repository history and propose evidence-backed closures for user approval. Use only on an explicit doctor request; an omitted project opens project selection.
argument-hint: "[project-ref]"
disable-model-invocation: true
---

# Nestor Doctor

Find tasks whose implementation has been merged into the repository but which remain open
in Nestor. Propose closing them and wait for the user's approval.

Run this workflow only on the user's explicit doctor request. Never start it on your own
initiative.

Use the Nestor skill for journal operations and the MCP catalogue for tool contracts.

## 1. Select the project and tasks

`/nestor-beta:doctor [project-ref]`

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

Start searching history at the earliest creation date among the audited tasks. Omit this
bound if a creation date is missing. For unresolved tasks, search older commit messages
for exact task references; inspect older diffs only when a reference or task evidence
points there. Code may predate a task recorded retrospectively.

Search commit messages and merged pull requests for exact task slugs or ids. Similar titles
are insufficient. Confirm that matching PRs delivered changes into the pinned integration
history. If PR search is unavailable, report that limitation and continue with commits.

## 3. Check completion

Propose closure only when both conditions are verified:

- A merged commit or PR explicitly references the task by slug or id.
- The implementation in the pinned tree satisfies all completion criteria in the task.
  Inspect the relevant code and diffs; a commit message alone is insufficient.

Leave uncertain or partially implemented tasks open for user review. This includes tasks
with vague criteria or requirements that cannot be verified from the repository.

For parent tasks, check all children, including those outside the audit's status selection.
Propose closing a parent only when every child is closed. Incomplete child information
requires user review. Put `need_review` tasks in the user-review group even if their
implementation appears complete.

## 4. Report and request approval

Present three groups:

- **Proposed closures:** task reference, title and supporting commits, PRs and code evidence.
- **Needs user review:** evidence found and the missing or uncertain criteria.
- **No evidence:** count of tasks for which no reference or implementation evidence was found.

Ask the user to approve the proposed closures or select individual tasks. Wait for their
answer before making changes. A general approval applies only to the proposed-closure
group; a task in the review group requires explicit selection.

## 5. Close approved tasks

Mark only the approved tasks as completed. If a task's scope or completion criteria changed
since the audit, return it to review before closing it.

Report confirmed closures, failures and any unknown outcomes. Leave all other tasks unchanged.

Do not edit repository files, create branches or commit as part of this workflow.
