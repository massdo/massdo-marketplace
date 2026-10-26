---
name: audit
description: Have an independent Codex or Claude agent audit one Nestor Plan or Task, or one pull request given by its number, with the agent, model and effort read from the arguments by their meaning, Codex sol6.1 at xhigh by default. For a Plan or Task, it audits the stored specification against the repository until the item is delivered, then the delivered code against that specification; the report is logged in a Nestor note linked to the audited item. For a pull request number, it audits that pull request's changes against its title and description. Use when the user or an agent asks to audit an item reference or a pull request number; an agent invokes it on its own with the same arguments and ends with the report as the result. Do not use for a review that the agent makes itself.
argument-hint: "<plan-or-task-id-or-slug|pr-number> [codex|claude] [model] [effort]"
---

# Nestor Audit

Have one Plan or Task, or one pull request, audited by a Codex or Claude agent that runs in
its own process, outside this conversation. The report on a Plan or Task is then logged in
a Nestor note linked to that item. The calling agent reads the item or the pull request,
pins the commits, writes the brief, waits for the end of the audit and records the report.
The auditor only reads the repository and has no access to the journal.

## Identify the plugin version

Pass `{ "version_hash": "21f7ec0e4b31c4f38" }` on every Nestor MCP call.

## 1. Invocation

- Claude Code: `/nestor-beta:audit <ref|PR> [agent] [model] [effort]`.
- Codex: `$nestor-beta:audit <ref|PR> [agent] [model] [effort]`.
- Cursor: select the skill, then supply the arguments.

An agent can also invoke the skill on its own, with the same arguments, when an audit is
asked of it: by its user in plain words, by its instructions, or by the agent that started
it, as for a subagent. It then follows these steps itself and ends with the report, which is
the result of the audit for whoever asked.

Read the arguments after the skill name, including a final `ARGUMENTS: …` line when the
client supplies one; an invocation without arguments takes them from the request that asked
for the audit. The first word is either a Nestor reference — an id, an id prefix or an exact
slug — or a pull request number: digits only, with or without a leading `#`. A number
audits that pull request of the workspace's repository, without any Nestor item: skip
sections 2 and 7.

Read the other words by their meaning, in any order, case or abbreviation, to choose the
agent that audits, its model and its effort:

| Agent | Families | Latest model, for `best` or no version | Efforts |
| --- | --- | --- | --- |
| `codex`, the Codex CLI | `sol`, `astra` | `gpt-6.1-sol` (sol6.1), `gpt-6-astra` (astra 6) | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `claude`, Claude Code | `opus`, `fable`, `sonnet`, `haiku` | the family name, which Claude Code resolves | `low`, `medium`, `high`, `xhigh`, `max` |

A model family alone names its agent, and `codex` without a family runs sol. A version the
words name runs that model, such as `sol 6` for `gpt-6-sol` or `opus 5.5` for
`claude-opus-5-5`. Without an agent or a model, the audit runs sol6.1; without an effort, it
runs at `xhigh`.

| Words | Audit |
| --- | --- |
| `codex sol best max` | sol6.1 at max |
| `claude op best max` | the latest Opus at max |
| `codex astra` | astra 6 at xhigh |
| `claude fable best` | the latest Fable at xhigh |

Without a reference or a number, ask for one in one line and stop. When a word means
nothing here, when the words name two agents, models or efforts, or a model or effort that
the agent does not offer, such as `claude sol` or `claude ultra`, or when they name
`claude` without a family, ask in one line for the intended choice with the accepted values
and stop there. Launch and write nothing before a valid choice comes back.

## 2. Read the item

Read the reference with `get_item`, passing it in `ref` with the global `scope`, `known` and
`version_hash`; `known` is null unless the item's complete content is already held with its
matched pair. Only a Plan or a Task, code or ordinary, can be audited: refuse a note or a
transmission. An archived or trashed item cannot receive a link: stop before launching the
audit.

- For a code Task attached to a Plan, follow its `planId`, then each `parentPlanId`, up to
  the root Plan. For a sub-plan, follow each `parentPlanId` up to the root Plan.
- For a Plan, or a code Task attached to one, read the whole subtree of the root Plan with
  `get_tree`, with that root as `rootItemId`, `depth` 6 and `verbose`. Follow `truncated`
  and every non-zero `hiddenChildCount` with further `get_tree` reads from the incomplete
  nodes until no member is missing. Then read every member's complete content with
  `get_item`, at most five references per call.

The effective Git context is the root Plan's, otherwise the autonomous code Task's. An
ordinary Task has none.

## 3. Check the repository

Work from the root of the workspace's Git repository. Its `origin`, in HTTPS form without
`.git`, must equal the effective Git context's `repository`; otherwise stop and say to run
the audit again from a checkout of that repository. Without an effective repository,
audit the workspace's repository; without a Git repository, stop.

Run `git fetch --prune origin`. Then never switch branches, stash or modify the working tree.

## 4. Choose the mode

The calling agent chooses the mode from the effective Git context and resolves every commit
it gives the auditor to a full SHA.

- With `git.pullRequestUrl`, read
  `gh pr view <url> --json state,baseRefName,headRefOid,mergeCommit`. Unless it was closed
  without a merge, fetch its head with `git fetch origin pull/<number>/head`, the number
  being the last segment of its URL, which also reaches the branch of a fork or a deleted
  branch. Check that `git rev-parse FETCH_HEAD` is `headRefOid`; otherwise read the pull
  request again.
  - OPEN: base is `git merge-base origin/<baseRefName> <headRefOid>`, head is `headRefOid`.
  - MERGED: base is `git merge-base <mergeCommit>^1 <headRefOid>`, head is `headRefOid`,
    whether the pull request was merged with a merge commit, squashed or rebased.
  - CLOSED without a merge: nothing is delivered.
  - If the pull request cannot be read, stop and say so.
- Otherwise, when `git.workBranch` exists on `origin`: base is the merge base of
  `origin/<targetBranch>`, or of `origin`'s default branch, and `origin/<workBranch>`; head
  is `origin/<workBranch>`.

When a delivery is found, the audit runs in code mode on the changes `git diff <base> <head>`.
Otherwise it runs in spec mode against the SHA of `origin/<targetBranch>`, or of `origin`'s
default branch as `git ls-remote --symref origin HEAD` names it.

A code Task attached to a Plan, or a sub-plan, shares the root Plan's pull request and work
branch with its siblings, so they do not prove its own delivery. It counts as delivered only
once its own work is: a Task whose `completionEvidence` records a commit and a pull request,
a sub-plan with at least one such code Task. Until then, it runs in spec mode.

A pull request number always runs in code mode. Its URL is the workspace's `origin`, in
HTTPS form without `.git`, followed by `/pull/<number>`. Read it as above, adding `title`
and `body` to the `--json` fields, and pin base and head the same way. A pull request closed
without a merge leaves nothing to audit: stop and say so.

## 5. Write the brief

Create a new private temporary directory with `mktemp -d` and write the brief to `brief.md`
there. The auditor starts from this brief alone: it holds only the stored content of the
audited work, the Nestor item's or the pull request's, and the audit instructions, never
this conversation or an opinion of the work, whether the calling agent's or that of whoever
asked for the audit.

- The audited item: its type, slug, title and status.
- Its stored content as is: body, specification, dependencies with their justifications and
  completionEvidence; for a Plan, the same for each member.
- For a code Task attached to a Plan, or a sub-plan, the root Plan and each of its other
  members with the same content, given as context only.
- For a pull request number, in place of the item and its content: the pull request's
  number, URL, title and description as is.
- The repository, the mode and the pinned SHAs.
- The language of the report, named explicitly: the user's language or, when an agent asked
  for the audit, the language that agent names, otherwise the language of its request.

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
- For a code Task attached to a Plan, or a sub-plan, judge only the audited item. The root
  Plan and its other members are context: in code mode, their changes in the diff are
  neither issues nor outside the scope.
- Read the code through Git at the given SHAs (`git show`, `git grep`, `git diff`), never
  in the working tree, which may hold unrelated local changes.
- Ask no question.
- End with a last message that is the report alone, written in the language that the brief
  names, in three blocks titled in that language, such as ISSUES, EXAMPLE and SOLUTIONS in
  English or ENJEUX, EXEMPLE and SOLUTIONS in French: one line per issue, the most important
  first; a single concrete example in two or three sentences; numbered solutions, one
  imperative action per line. No file paths and no detailed evidence. Keep only the issues that occur
  in the nominal flow, never one built on an unfavorable scenario that nothing establishes.
  Without any issue, a single line under the first heading says so.

## 6. Launch the audit

Before writing the brief, check that the agent's command, `codex` or `claude`, is on the
PATH. Without it, stop before any write and say that the audit requires that CLI, installed
and signed in.

Run the agent's command from the repository root, with the brief's directory as `<dir>` and
the effort of section 1 as `<effort>`.

For Codex, `<model>` is the model of section 1, such as `gpt-6.1-sol` or `gpt-6-astra`,
`<repo-root>` is the repository root, and `<skills-off>` holds one
`{path="<file>",enabled=false}` entry, comma separated, for each file that
`find -L ~/.codex/skills ~/.agents/skills -name SKILL.md` returns:

```sh
codex exec --ignore-user-config -c 'skills.bundled.enabled=false' -c 'skills.config=[<skills-off>]' --model <model> --config 'model_reasoning_effort="<effort>"' --sandbox read-only --cd <repo-root> --output-last-message <dir>/report.md - < <dir>/brief.md > <dir>/audit.log 2>&1
```

`--ignore-user-config` keeps the user's memories, MCP servers, plugins and hooks out of the
audit: nothing from another session enters it, and the auditor cannot write to the journal.
Codex keeps its own sign-in. It still loads skills without that configuration, so the two
`skills` overrides turn off its bundled skills and each of the user's own; a whole skills
folder cannot be turned off at once. `--sandbox read-only` lets the auditor change nothing
and gives it no network, which is why the calling agent fetches and pins the commits
beforehand.

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
the audit ends, run it in the background and resume when it ends. On the user's invocation,
say meanwhile in one sentence that the audit is running, with the agent and its model, the
cited item or the pull request, and the path of `audit.log`. When an agent invoked the skill
on its own, keep waiting for the process within the same turn and write nothing before the
report: whoever asked, such as the agent that started a subagent, may receive only what the
turn ends with.

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

At the end, give the report as is to whoever asked for the audit, the user or an agent, then
one sentence that cites the note and the audited item using Nestor's item citation rule;
after a pull request audit, that sentence links the pull request instead. Do not narrate the
calls, versions, ETags or any technical identifier beyond those citations.
