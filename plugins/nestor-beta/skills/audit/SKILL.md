---
name: audit
description: Have an independent Codex agent audit one Nestor Plan or Task, sol6.1 or astra at the chosen reasoning effort, sol6.1 xhigh by default. Before anything is delivered, it audits the stored specification against the repository; once a pull request or a work branch exists, it audits the delivered code against that specification. The report is logged in a Nestor note linked to the audited item. Use only when the user explicitly invokes audit with an item reference; an agent, plan, task or another skill must never invoke it.
argument-hint: "<plan-or-task-id-or-slug> [sol6.1|astra] [low|medium|high|xhigh|max|ultra]"
disable-model-invocation: true
---

# Nestor Audit

Have one Plan or Task audited by a Codex agent that runs in its own process, outside this
conversation, then log its report in a Nestor note linked to that item. The calling agent
reads the item, pins the commits, writes the brief, waits for the end of the audit and
records the report. The auditor only reads the repository and has no access to the journal.

## Identify the plugin version

Pass `{ "version_hash": "2f446e153084ebf2a" }` on every Nestor MCP call.

## 1. Invocation

- Claude Code: `/nestor-beta:audit <ref> [model] [effort]`.
- Codex: `$nestor-beta:audit <ref> [model] [effort]`.
- Cursor: select the skill, then supply the arguments.

Run only on that explicit invocation. Read the arguments after the skill name, including a
final `ARGUMENTS: …` line when the client supplies one. The first word is the reference: an
id, an id prefix or an exact slug. Each following word, in any order and in any case, is a
model, `sol6.1` or `astra`, or an effort, `low`, `medium`, `high`, `xhigh`, `max` or
`ultra`, with at most one model and one effort. The defaults are `sol6.1` and `xhigh`.
`sol6.1` runs the Codex model `gpt-6.1-sol`; `astra` runs `gpt-6-astra`.

Without a reference, ask for it in one line and stop. On an unknown word, or a second model
or effort, stop and name that word and the accepted values, without launching or writing
anything.

## 2. Read the item

Read the reference with `get_item`, passing it in `ref` with the global `scope`, `known` and
`version_hash`; `known` is null unless the item's complete content is already held with its
matched pair. Only a Plan or a Task, code or ordinary, can be audited: refuse a note or a
transmission. An archived or trashed item cannot receive a link: stop before launching the
audit.

- For a Plan, read its whole subtree with `get_tree`, with the Plan as `rootItemId`, `depth`
  6 and `verbose`. Follow `truncated` and every non-zero `hiddenChildCount` with further
  `get_tree` reads from the incomplete nodes until no member is missing. Then read every
  member's complete content with `get_item`, at most five references per call.
- For a code Task attached to a Plan, or a sub-plan, follow its `planId`, then each
  `parentPlanId`, up to the root Plan.

The effective Git context is the root Plan's, otherwise the autonomous code Task's. An
ordinary Task has none.

## 3. Check the repository

Work from the root of the workspace's Git repository. Its `origin`, in HTTPS form without
`.git`, must equal the effective Git context's `repository`; otherwise stop and ask the user
to run the audit again from a checkout of that repository. Without an effective repository,
audit the workspace's repository; without a Git repository, stop.

Run `git fetch --prune origin`. Then never switch branches, stash or modify the working tree.

## 4. Choose the mode

The calling agent chooses the mode from the effective Git context and resolves every commit
it gives the auditor to a full SHA.

- With `git.pullRequestUrl`, read
  `gh pr view <url> --json state,baseRefName,headRefOid,mergeCommit`:
  - OPEN: base is `git merge-base origin/<baseRefName> <headRefOid>`, head is `headRefOid`.
  - MERGED: base is `<mergeCommit>^1`, head is `<mergeCommit>`.
  - CLOSED without a merge: nothing is delivered.
  - If the pull request cannot be read, stop and say so.
- Otherwise, when `git.workBranch` exists on `origin`: base is the merge base of
  `origin/<targetBranch>`, or of `origin`'s default branch, and `origin/<workBranch>`; head
  is `origin/<workBranch>`.

When a delivery is found, the audit runs in code mode on the changes `git diff <base> <head>`.
Otherwise it runs in spec mode against the SHA of `origin/<targetBranch>`, or of `origin`'s
default branch as `git ls-remote --symref origin HEAD` names it.

## 5. Write the brief

Create a new private temporary directory with `mktemp -d` and write the brief to `brief.md`
there. The auditor starts from this brief alone: it holds only the content stored in Nestor
and the audit instructions, never this conversation or the calling agent's opinion of the
work.

- The audited item: its type, slug, title and status.
- Its stored content as is: body, specification, dependencies with their justifications and
  completionEvidence; for a Plan, the same for each member.
- The repository, the mode and the pinned SHAs.
- The user's language, named explicitly.

In spec mode, the brief asks the auditor to check against the pinned SHA that the cited
files and symbols exist, that the steps are feasible and their verifications conclusive,
that the completion criteria are observable, that no decision is left to whoever builds the
work, that the dependencies are justified, and which risks the architecture carries.

In code mode, it asks the auditor to check `git diff <base> <head>` against the
specification: criteria not met, bugs and regressions, missing or weakened tests, and
changes outside the scope.

In both modes, the brief gives the auditor these rules:

- Stay read-only: no file, commit, push, pull request comment or journal entry.
- Read the code through Git at the given SHAs (`git show`, `git grep`, `git diff`), never
  in the working tree, which may hold unrelated local changes.
- Ask no question.
- End with a last message that is the report alone, written in the user's language, in
  three blocks titled in that language, such as ISSUES, EXAMPLE and SOLUTIONS in English or
  ENJEUX, EXEMPLE and SOLUTIONS in French: one line per issue, the most important first; a
  single concrete example in two or three sentences; numbered solutions, one imperative
  action per line. No file paths and no detailed evidence. Keep only the issues that occur
  in the nominal flow, never one built on an unfavorable scenario that nothing establishes.
  Without any issue, a single line under the first heading says so.

## 6. Launch the audit

Before writing the brief, check that `codex` is on the PATH. Without it, stop before any
write and say that the audit requires the Codex CLI, installed and signed in.

Run this command from the repository root, with `gpt-6.1-sol` or `gpt-6-astra` as
`<model>`, the effort of section 1 as `<effort>`, the repository root as `<repo-root>` and
the brief's directory as `<dir>`:

```sh
codex exec --ignore-user-config --model <model> --config 'model_reasoning_effort="<effort>"' --sandbox read-only --cd <repo-root> --output-last-message <dir>/report.md - < <dir>/brief.md > <dir>/audit.log 2>&1
```

`--ignore-user-config` keeps the user's memories, MCP servers, plugins and hooks out of the
audit: nothing from another session enters it, and the auditor cannot write to the journal.
Codex keeps its own sign-in. `--sandbox read-only` lets the auditor change nothing and gives
it no network, which is why the calling agent fetches and pins the commits beforehand.

Wait for the process to end without reading `audit.log`; only `report.md` comes back into
the conversation, at the end. When the client cannot keep a command in the foreground until
the audit ends, run it in the background and resume when it ends; then say in one sentence
that the audit is running, with the agent, the cited item and the path of `audit.log` to
follow it.

On a non-zero exit or an empty `report.md`, write no note: say that the audit failed, give
its cause in plain words, read from the end of the log, and the log's path.

## 7. Log the report

Create the note with `create_item`, type `note`, in the audited item's scope: `project` with
its project, otherwise global. Title it `Audit <sol6.1|astra> <effort> — <item title>`. Its
body is one header line, an empty line, then `report.md` as is. The header line gives the
local date and time, the agent with its model, the mode, the item's slug, the repository,
the audited SHAs and, in code mode, the pull request URL when there is one.

Then call `update_item` with `add_link` in the same scope, passing the note as `id` with the
pair that `create_item` returned, the note as `sourceId` and the audited item as `targetId`:
`kind` `documents` for a Task, `related-to` for a Plan. Change nothing else on the audited
item: not its status, body, specification, tags or approval.

If the creation is refused, say that the report is not logged and give the path of
`report.md`. If the link is refused, the note stays: cite it and say that it is not linked.

## 8. Report

At the end, show the report as is, then one sentence that cites the note and the audited
item using Nestor's item citation rule. Do not narrate the calls, versions, ETags or any
technical identifier beyond those citations.
