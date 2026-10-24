---
name: audit
description: Have an independent Codex or Claude agent audit one Nestor Plan or Task, or one pull request given by its number, with the agent, model and effort read from the arguments by their meaning, Codex sol6.1 at xhigh by default. For a Plan or Task, it audits the stored specification against the repository before anything is delivered, and the delivered code against that specification once a pull request or a work branch exists; the report is logged in a Nestor note linked to the audited item. For a pull request number, it audits that pull request's changes against its title and description. Use only when the user explicitly invokes audit with an item reference or a pull request number; an agent, plan, task or another skill must never invoke it.
argument-hint: "<plan-or-task-id-or-slug|pr-number> [codex|claude] [model] [effort]"
disable-model-invocation: true
---

# Nestor Audit

Have one Plan or Task, or one pull request, audited by a Codex or Claude agent that runs in
its own process, outside this conversation. The report on a Plan or Task is then logged in
a Nestor note linked to that item. The calling agent reads the item or the pull request,
pins the commits, writes the brief, waits for the end of the audit and records the report.
The auditor only reads the repository and has no access to the journal.

## Identify the plugin version

Pass `{ "version_hash": "2f446e153084ebf2a" }` on every Nestor MCP call.

## 1. Invocation

- Claude Code: `/nestor-beta:audit <ref|PR> [agent] [model] [effort]`.
- Codex: `$nestor-beta:audit <ref|PR> [agent] [model] [effort]`.
- Cursor: select the skill, then supply the arguments.

Run only on that explicit invocation. Read the arguments after the skill name, including a
final `ARGUMENTS: …` line when the client supplies one. The first word is either a Nestor
reference — an id, an id prefix or an exact slug — or a pull request number: digits only,
with or without a leading `#`. A number audits that pull request of the workspace's
repository, without any Nestor item: skip sections 2 and 7.

Read the other words by their meaning, in any order, case or abbreviation, to choose the
agent that audits, its model and its effort:

- Agent: `codex` runs the Codex CLI, `claude` runs Claude Code. A model family alone names
  its agent.
- Codex families: `sol`, whose latest model is `gpt-6.1-sol` (sol6.1), and `astra`, whose
  latest is `gpt-6-astra` (astra 6). `codex` without a family runs sol.
- Claude families: `opus`, `fable`, `sonnet` and `haiku`.
- `best`, or no version, runs the family's latest model. A version the user names runs that
  model, such as `sol 6` for `gpt-6-sol` or `opus 5.5` for `claude-opus-5-5`.
- Efforts: `low`, `medium`, `high`, `xhigh` and `max`, plus `ultra` for Codex.

Without an agent or a model, the audit runs sol6.1; without an effort, it runs at `xhigh`.
So `codex sol best max` is sol6.1 at max, `claude op best max` is the latest Opus at max,
`codex astra` is astra 6 at xhigh and `claude fable best` is the latest Fable at xhigh.

Without a reference or a number, ask for one in one line and stop. When a word means
nothing here, when the words name two agents, models or efforts, or a model or effort that
the agent does not offer, such as `claude sol` or `claude ultra`, or when they name
`claude` without a family, ask in one line for the intended choice with the accepted values
and wait for the answer. Launch and write nothing before it.

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
- For a code Task attached to a Plan, follow its `planId`, then each `parentPlanId`, up to
  the root Plan. For a sub-plan, follow each `parentPlanId` up to the root Plan.

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

A pull request number always runs in code mode. Its URL is the workspace's `origin`, in
HTTPS form without `.git`, followed by `/pull/<number>`. Read it as above, adding `title`
and `body` to the `--json` fields, and pin base and head the same way. A pull request closed
without a merge leaves nothing to audit: stop and say so.

## 5. Write the brief

Create a new private temporary directory with `mktemp -d` and write the brief to `brief.md`
there. The auditor starts from this brief alone: it holds only the stored content of the
audited work, the Nestor item's or the pull request's, and the audit instructions, never
this conversation or the calling agent's opinion of the work.

- The audited item: its type, slug, title and status.
- Its stored content as is: body, specification, dependencies with their justifications and
  completionEvidence; for a Plan, the same for each member.
- For a pull request number, in place of the item and its content: the pull request's
  number, URL, title and description as is.
- The repository, the mode and the pinned SHAs.
- The user's language, named explicitly.

In spec mode, the brief asks the auditor to check against the pinned SHA that the cited
files and symbols exist, that the steps are feasible and their verifications conclusive,
that the completion criteria are observable, that no decision is left to whoever builds the
work, that the dependencies are justified, and which risks the architecture carries.

In code mode, it asks the auditor to check `git diff <base> <head>` against the
specification, or against the pull request's title and description for a pull request
number: criteria not met, bugs and regressions, missing or weakened tests, and changes
outside the scope.

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

Before writing the brief, check that the agent's command, `codex` or `claude`, is on the
PATH. Without it, stop before any write and say that the audit requires that CLI, installed
and signed in.

Run the agent's command from the repository root, with the brief's directory as `<dir>` and
the effort of section 1 as `<effort>`.

For Codex, `<model>` is the model of section 1, such as `gpt-6.1-sol` or `gpt-6-astra`, and
`<repo-root>` is the repository root:

```sh
codex exec --ignore-user-config --model <model> --config 'model_reasoning_effort="<effort>"' --sandbox read-only --cd <repo-root> --output-last-message <dir>/report.md - < <dir>/brief.md > <dir>/audit.log 2>&1
```

`--ignore-user-config` keeps the user's memories, MCP servers, plugins and hooks out of the
audit: nothing from another session enters it, and the auditor cannot write to the journal.
Codex keeps its own sign-in. `--sandbox read-only` lets the auditor change nothing and gives
it no network, which is why the calling agent fetches and pins the commits beforehand.

For Claude, `<model>` is the family name, which Claude Code resolves to its latest model, or
the full name of the version the user named:

```sh
claude -p --safe-mode --setting-sources "" --model <model> --effort <effort> --tools Bash --allowedTools "Bash(git ls-tree *)" --permission-mode dontAsk --no-session-persistence < <dir>/brief.md > <dir>/report.md 2> <dir>/audit.log
```

`--safe-mode` and the empty `--setting-sources` keep the user's CLAUDE.md files, memory,
settings, plugins, hooks and MCP servers out of the audit: nothing from another session
enters it, and the auditor cannot write to the journal. Claude Code keeps its own sign-in.
`--tools Bash` with `--permission-mode dontAsk` leaves the auditor only the commands that
change nothing: Git reads run, while file writes and network requests are refused without
waiting for an approval. `--allowedTools` adds `git ls-tree`, a read that Claude Code does
not count among them. `--no-session-persistence` keeps the audit out of the user's
sessions.

Wait for the process to end without reading `audit.log`; only `report.md` comes back into
the conversation, at the end. When the client cannot keep a command in the foreground until
the audit ends, run it in the background and resume when it ends; then say in one sentence
that the audit is running, with the agent and its model, the cited item or the pull
request, and the path of `audit.log`.

On a non-zero exit or an empty `report.md`, write no note: say that the audit failed and give
its cause in plain words with the path of the file it comes from, the end of `audit.log`, or
`report.md` for Claude, which prints its errors there.

## 7. Log the report

Create the note with `create_item`, type `note`, in the audited item's scope: `project` with
its project, otherwise global. Title it `Audit <model> <effort> — <item title>`, with the
model as section 1 reads it, such as `sol6.1`, `astra 6` or `opus`. Its body is one header
line, an empty line, then `report.md` as is. The header line gives the local date and time,
the agent with its model, the mode, the item's slug, the repository, the audited SHAs and,
in code mode, the pull request URL when there is one.

Then call `update_item` with `add_link` in the same scope, passing the note as `id` with the
pair that `create_item` returned, the note as `sourceId` and the audited item as `targetId`:
`kind` `documents` for a Task, `related-to` for a Plan. Change nothing else on the audited
item: not its status, body, specification, tags or approval.

If the creation is refused, say that the report is not logged and give the path of
`report.md`. If the link is refused, the note stays: cite it and say that it is not linked.

## 8. Report

At the end, show the report as is, then one sentence that cites the note and the audited
item using Nestor's item citation rule; after a pull request audit, that sentence links the
pull request instead. Do not narrate the calls, versions, ETags or any technical identifier
beyond those citations.
