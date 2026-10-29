# Audit a pull request

A pull request number audits that pull request of the workspace's repository, without any
Nestor item: it always runs in code mode, on its changes against its title and description,
and logs no note.

## Read the pull request

Work from the root of the workspace's Git repository; without a Git repository, stop. The
pull request's URL is the workspace's `origin`, in HTTPS form without `.git`, followed by
`/pull/<number>`.

Run `git fetch --prune origin`. Then never switch branches, stash or modify the working tree.

Read `gh pr view <url> --json state,baseRefName,headRefOid,mergeCommit,title,body`. Unless
it was closed without a merge, fetch its head with `git fetch origin pull/<number>/head`,
which also reaches the branch of a fork or a deleted branch. Check that
`git rev-parse FETCH_HEAD` is `headRefOid`; otherwise read the pull request again.

The calling agent resolves every commit it gives the auditor to a full SHA:

- OPEN: base is `git merge-base origin/<baseRefName> <headRefOid>`, head is `headRefOid`.
- MERGED: base is `git merge-base <mergeCommit>^1 <headRefOid>`, head is `headRefOid`,
  whether the pull request was merged with a merge commit, squashed or rebased.
- CLOSED without a merge: nothing is left to audit. Stop and say so.
- If the pull request cannot be read, stop and say so.

## Write the pull request's part of the brief

The brief holds the pull request's number, URL, title and description as is. The audit
runs in code mode on `git diff <base> <head>`, and the reference that the diff is checked
against is that title and that description.

## Report

At the end, give the report as is to whoever asked for the audit, the user or an agent, then
one sentence that links the pull request. Do not narrate the calls or any technical
identifier beyond that link.
