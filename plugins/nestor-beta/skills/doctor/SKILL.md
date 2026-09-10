---
name: doctor
description: Audit a Nestor project's open tasks against merged repository history and propose evidence-backed closures for user approval. Use only on an explicit doctor request; an omitted project opens project selection.
disable-model-invocation: true
user-invocable: false
---

# Nestor Doctor

Find tasks whose implementation has been merged into the repository but which remain open
in Nestor. Propose closing them and wait for the user's approval.

Use the Nestor skill for journal operations and the MCP catalogue for tool contracts.

## 1. Select the project and tasks

`/nestor-beta:doctor [project-ref]`

If no project is supplied, show the active projects and wait for the user to select one.
Confirm that the selected project corresponds to the repository being audited.

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
