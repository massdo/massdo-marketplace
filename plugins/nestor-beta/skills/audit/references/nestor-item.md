# Audit a Nestor Plan or Task

The audit of a Plan or a Task reads the item, pins the commits from its Git context, writes
the part of the brief proper to the item and, once the report comes back, logs it in a
Nestor note linked to the item.

## Read the item

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

## Check the repository

Work from the root of the workspace's Git repository. Its `origin`, in HTTPS form without
`.git`, must equal the effective Git context's `repository`; otherwise stop and say to run
the audit again from a checkout of that repository. Without an effective repository,
audit the workspace's repository; without a Git repository, stop.

Run `git fetch --prune origin`. Then never switch branches, stash or modify the working tree.

## Choose the mode

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

## Write the item's part of the brief

The brief holds:

- The audited item: its type, slug, title and status.
- Its stored content as is: body, specification, dependencies with their justifications and
  completionEvidence; for a Plan, the same for each member.
- For a code Task attached to a Plan, or a sub-plan, the root Plan and each of its other
  members with the same content, given as context only.

In code mode, the reference that the diff is checked against is the audited item's
specification.

In spec mode, the brief asks the auditor to check against the pinned SHA that the cited
files and symbols exist, that the steps are feasible and their verifications conclusive,
that the completion criteria are observable, that no decision is left to whoever builds the
work, that the dependencies are justified, and which risks the architecture carries.

For a code Task attached to a Plan, or a sub-plan, the brief also gives the auditor this
rule: judge only the audited item. The root Plan and its other members are context: in code
mode, their changes in the diff are neither issues nor outside the scope.

## Log the report

Once the mode file returns the report, create the note with `create_item`, type `note`, in
the audited item's scope: `project` with its project, otherwise global. Title it
`Audit <model> <effort> — <item title>`, with the model and the effort that the mode file
chose, as it reads them, such as `sol6.1`, `astra 6` or `opus`; leave out each one that it
did not choose, down to `Audit — <item title>` when it chose neither. Its body is one header
line, an empty line, then the report as is. The header line gives the local date and time,
the client that ran the subagent or the CLI command, the model and the effort when chosen,
the mode, the item's slug, the repository, the audited SHAs and, in code mode, the pull
request URL when there is one.

Then call `update_item` with `add_link` in the same scope, passing the note as `id` with the
pair that `create_item` returned, the note as `sourceId` and the audited item as `targetId`:
`kind` `documents` for a Task, `related-to` for a Plan. Change nothing else on the audited
item: not its status, body, specification, tags or approval.

If the creation is refused, say that the report is not logged. If the link is refused, the
note stays: cite it and say that it is not linked.

## Report

At the end, give the report as is to whoever asked for the audit, the user or an agent, then
one sentence that cites the note and the audited item using Nestor's item citation rule. Do
not narrate the calls, versions, ETags or any technical identifier beyond those citations.
