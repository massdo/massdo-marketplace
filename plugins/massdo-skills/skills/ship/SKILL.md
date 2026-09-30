---
name: ship
description: Review the open pull requests of the current GitHub repository, propose which ones to merge into main, then recognize and follow the repository's own release procedure. Use it when the user wants to ship, land or release pending work — "ship it", "merge the open PRs", "what can go to main", "cut a release" — in any language, even without naming the skill. Invoke it as /massdo-skills:ship or $massdo-skills:ship; it takes no argument and only targets main. It needs Git and the GitHub CLI. Preparing the diagnosis is free; every merge, tag, workflow run or publication waits for the user's agreement at that moment.
---

# Ship

Turn "what is open on this repository" into a diagnosis, then a proposal, and — only once the
user agrees — into merges on `main`, followed by the release procedure the repository already
has. Git and the GitHub CLI (`gh`) are all it needs.

The user decides every action that cannot be undone. Your part is to make that decision easy
and safe: look at everything there is to see, say what you found and what you could not see,
and ask when each action comes up rather than once at the start.

## Identify the plugin version

Pass `{ "version_hash": "59c512fbfdbc669c" }` on every Nestor MCP call.

## Scope and consent

- **The target is `main`, and only `main`.** The skill takes no argument and never asks which
  branch to ship to; text written after the skill name is part of the user's message, not a
  target. When `main` does not exist on the remote, explain the blocker and stop. Never fall
  back to another branch: that would be choosing the target on the user's behalf.
- **An invocation prepares a diagnosis and a proposal, nothing more.** It is not agreement to
  merge every pull request, and not agreement to publish a release. Ask at the moment of each
  action that changes something beyond this machine: a merge, a tag push, a workflow run, a
  script run, a release creation. An agreement already given in the session holds for its
  exact scope — those pull requests, those head commits, that action — and for nothing wider.
- **A release is a conditional step.** Follow the procedure the repository already has, and
  trigger no deployment beyond the effects its own workflows already announce.
- **Report what you observed.** A pull request is open, queued for merge or merged; a tag
  exists or it does not; a release is published or it is not. Never report one as another.
- **Write in the language the user writes in.** These instructions are in English, which says
  nothing about the language of your replies.

## 1. Take inventory

Start from the evidence, not from the user's description of it.

1. **Resolve the repository exactly.** Run
   `gh repo view --json nameWithOwner,url,isFork,parent,defaultBranchRef` and `git remote -v`.
   Keep the resulting `OWNER/REPO` and pass it as `--repo` to every later `gh` call, so that
   no command depends on an implicit default. A fork, or remotes that point at different
   repositories, leave the target ambiguous: name the candidates and ask. When this is not a
   GitHub repository, or `gh` is not authenticated, say so and stop.
2. **Refresh the remote state.** Run `git fetch --prune` on the remote that points at that
   repository (usually `origin`). Then confirm that `main` exists both as a remote-tracking
   branch and on GitHub: `git rev-parse --verify refs/remotes/origin/main` and
   `gh api repos/OWNER/REPO/branches/main --jq .commit.sha`. Record that SHA as the baseline
   every later check refers to. If `main` is absent, that is the blocker described in
   "Scope and consent".
3. **Read every open pull request.** `gh pr list` returns 30 results by default and does not
   say when it stops, so walk every page:
   `gh api --paginate "repos/OWNER/REPO/pulls?state=open&per_page=100" --jq '.[] | [.number, .base.ref, .draft, .head.sha[0:7], .title] | @tsv'`.
   State how many you read.
4. **Split them.** The pull requests whose base is `main` are the candidates. The others,
   whose base is another branch — often one that stacks on a candidate — are out of
   selection: list them anyway, with the base they target.
5. **Look at this machine.** `git worktree list --porcelain` lists the worktrees. For each
   reachable one, `git -C <path> status --porcelain=v1 --branch` shows uncommitted changes
   and `git -C <path> log --oneline HEAD --not --remotes` the commits that no remote branch
   contains yet, a detached worktree included. `git log --oneline --branches --not --remotes`
   covers the local branches checked out nowhere. Having no upstream does not make a branch
   unpushed, since its commits may already sit on another remote branch: these two are the
   test. Keep the summary short: name the worktrees that hold uncommitted changes or unpushed
   commits, and count the clean ones instead of listing them.

Present what you found, and say what you could not see. You see this machine's clones and
worktrees and GitHub's state. You do not see another agent's unsaved work, another machine,
or a session that has not pushed; say so instead of implying the picture is complete.

## 2. Verify each pull request

For each candidate, read the evidence that decides whether it can land on `main` as it stands
now.

```bash
gh pr view N --repo OWNER/REPO --json number,title,url,isDraft,headRefName,headRefOid,mergeable,mergeStateStatus,reviewDecision,latestReviews,reviewRequests,statusCheckRollup
gh pr checks N --repo OWNER/REPO --required
gh pr diff N --repo OWNER/REPO
```

- **Draft.** `isDraft` true means not ready. Read that field itself rather than inferring a
  draft from `mergeStateStatus`.
- **Conflicts.** `mergeable` must be `MERGEABLE`; `CONFLICTING` is blocked. GitHub computes
  mergeability lazily, so `UNKNOWN` only means it has not been computed yet: read again after
  a few seconds, a few times. Still `UNKNOWN` means unknown, and unknown is not a green light.
- **Merge state.** `mergeStateStatus` must be `CLEAN`. `BEHIND` (the repository requires the
  branch to be up to date), `BLOCKED`, `DIRTY`, `UNSTABLE` and `UNKNOWN` are reported with
  what they mean, never rounded up. Bringing someone's branch up to date is a write to it and
  needs its own agreement.
- **Checks.** `gh pr checks --required` lists the checks this pull request must pass. What
  `main` requires is also in `gh api repos/OWNER/REPO/branches/main/protection` and
  `gh api repos/OWNER/REPO/rules/branches/main`; a refusal (403, 404) means unknown, not
  none. Every required check must have concluded successfully **on the current head commit**
  (`headRefOid`) — a run on an earlier head does not count. Pending, failed, cancelled,
  skipped or missing is not green, and a required check that never ran is the quiet one. When
  nothing is required, say so: there is no automated evidence, and the proposal must not
  imply any.
- **Reviews.** `reviewDecision` `CHANGES_REQUESTED` or `REVIEW_REQUIRED` is blocked. An empty
  value means no review rule applies; say whether anyone reviewed.
- **Dependencies between pull requests.** A base branch that is another pull request's head,
  a "depends on #N" in a description, two pull requests editing the same lines or bumping the
  same version: each one fixes an order, or means the later pull request needs attention once
  the earlier one has merged.
- **Work in progress.** Uncommitted changes or unpushed commits in a worktree on the
  candidate's branch (`headRefName`) mean the remote head may not be what its author means to
  ship. Say so in its reason, and ask about it in the proposal.
- **The diff.** It is what lands on `main`. Read it for what the title does not say — a
  changed workflow or release file, anything that contradicts the description.

An unknown state, a required check that is absent or inconclusive, a missing required review,
or a conflict is never a green light.

Give a table of the pull requests in three groups — **ready**, **blocked**, **out of
selection** — with the link, the head commit you checked, and the reason for each. A reason
cites its evidence:

| Pull request | Group | Head | Reason |
|---|---|---|---|
| [#12 Add export](https://github.com/OWNER/REPO/pull/12) | ready | `a1b2c3d` | required check `validate` passed on this head; mergeable; no review rule |
| [#14 Rework auth](https://github.com/OWNER/REPO/pull/14) | blocked | `e4f5a6b` | draft; conflicts with `main`; required check `validate` failed on this head |
| [#15 Docs on #12](https://github.com/OWNER/REPO/pull/15) | out of selection | `c7d8e9f` | its base is `feature/export`, not `main` |

Do not stash, discard, force-push, resolve a conflict, or bring local commits into a pull
request without a separate authorization. When a check needs a checkout, use a clean,
temporary worktree at the head commit under examination, outside the user's working tree, and
remove it afterwards.

## 3. Recognize the release procedure — before any merge

Do this before proposing a merge, because a merge may itself start a release, and the user has
to hear that before agreeing.

**Where to look.** The repository's agent and contributor files (`AGENTS.md`, `CLAUDE.md`,
`CONTRIBUTING.md`), `README.md`, the scripts in `package.json` and `Makefile`, and any
publishing configuration. Then `.github/workflows/*.yml` and `*.yaml`, read where they will
act: on the remote `main` (`git show origin/main:<path>`), and, for every workflow or release
file a selected pull request adds, edits or deletes, in that pull request
(`git fetch origin pull/N/head`, then `git show <headRefOid>:<path>`) — once it merges, that
is what `main` runs. A workflow file can exist and be disabled:
`gh workflow list --repo OWNER/REPO --all` says which ones are active.

**How to read them.** Follow the chain: trigger → conditions → steps (`run`, `uses`) → the
scripts, actions and reusable workflows those call → real effect. Note branch, tag and path
filters, `if`, `needs`, inputs, environments and the authorization they require — the names
of secrets and approvals, never their values. Then say which of these it is: a tag, a GitHub
Release, a package publication, a version notification, a deployment. A name with `release`
or `publish` in it is a hint, not a finding: a script called `publish_…` that only sends
version documents to a catalog service is a notification, and a workflow that reacts to
`release: published` does not create the release it reacts to.

**How to conclude.** Cite the file and line behind each conclusion
(`git show <ref>:<path> | nl -ba` shows the numbers). A procedure you cannot establish stays
uncertain. Never run a publishing command to find out what it does.

Then act on the procedure you found:

- **It publishes automatically after a merge into `main`.** Announce the effect in the merge
  proposal, before the user agrees; after the merge, follow the workflow and check what it
  did. Read its conditions: a release workflow on `main` does not mean every merge publishes —
  filters, `if` conditions and version guards decide.
- **It publishes when a tag is pushed.** After the merges and their validation, prepare the
  version, the exact tag, the notes and the documented command. Ask before creating or
  pushing the tag, unless an agreement already covers it.
- **It is a manual workflow (`workflow_dispatch`).** Prepare the workflow, the ref and the
  exact inputs, then propose launching it.
- **It is a documented command or script.** Understand its effects and prerequisites, prepare
  the invocation, then propose running it.
- **It reacts to a release (`release` with `types: [published]`).** That trigger says what
  happens after a release is published, not who publishes it. Find what creates the release;
  until you have, the procedure is uncertain.
- **There is no procedure, several that contradict each other, or a dependency you cannot
  reach.** Report the uncertainty and the decision that is missing. Do not invent a release
  mechanism or install one.

## 4. Propose, then merge

**The proposal.** Put in front of the user the repository, `main` with its baseline commit, the
selected pull requests with the head commits you verified, the merge order and why, the
validations done, the merge method, and the automatic effects each merge will have according
to the release procedure you found. Then wait for the user's agreement, unless one already
given in the session covers exactly this.

The method is the one the repository allows and documents: its merge settings
(`gh api repos/OWNER/REPO --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'`),
the rules on `main` (`gh api repos/OWNER/REPO/rules/branches/main` can restrict methods), and
its contributor documents. When several are allowed and none is documented, ask in the
proposal instead of choosing.

**The merges.** For each pull request, in the agreed order:

1. Read it again. Its head must still be the commit you verified, and its checks, reviews and
   mergeability must still hold.
2. Merge it locked on that commit:
   `gh pr merge N --repo OWNER/REPO --match-head-commit <headRefOid> --<method>`, where the
   method is `merge`, `squash` or `rebase`. GitHub refuses the merge if the branch moved since
   you verified it, so what lands is exactly what was examined.
3. Confirm the result:
   `gh pr view N --repo OWNER/REPO --json state,mergedAt,mergeCommit,autoMergeRequest`.
   Auto-merge and a merge queue only record a request. Wait for the real outcome before
   reporting a merge, and before starting the next one; a request still pending after a
   reasonable wait is reported as pending, not as merged.
4. Verify the remaining pull requests again, as in "Verify each pull request": `main` just
   moved, so one of them may now conflict, be behind, or have new checks running.

Respect GitHub's protections. Never use `--admin` to get around one; when a protection blocks
a merge, report it. Stop when the approved scope changes — a head commit moved, the user
changed the list — or a new verification fails, and report the partly delivered state: what
merged and at which commit, what did not and why. What remains goes back through a proposal
and needs a new agreement.

## 5. Finish

1. **Check `main`.** Fetch, then take the final commit of `main` and look at its runs:
   `gh run list --repo OWNER/REPO --commit <sha> --json databaseId,name,status,conclusion,event,url`.
   A workflow takes a moment to start, so read again when nothing shows yet. Wait for the ones
   the merge was expected to start with `gh run watch <id> --exit-status`, and report each
   result as it is.
2. **Prepare the release, when the procedure needs an action from you or the user** — a tag,
   a manual workflow, a documented command. Put a concrete proposal in front of the user
   before asking: the version and the tag, the commit, the notes, any assets, and the command
   exactly as the repository documents it. When the procedure needs edits first — a version
   bump, a changelog, a release pull request — prepare and present them here; opening or
   pushing them is an action that needs its own agreement. Never create a tag that disagrees
   with the versions the repository declares. `gh release create <tag>` creates the tag itself
   when it does not exist, so add `--verify-tag` when the tag is meant to exist already.
3. **Follow what was triggered.** Watch the workflows the merge or the tag started, then
   confirm the commit, the tag and the URL of the release or package, according to the effect
   you announced: `gh release view <tag> --json url,tagName,targetCommitish,isDraft` for a
   GitHub Release, `git ls-remote --tags origin <tag> '<tag>^{}'` for a tag (an annotated tag
   shows its own object, then the commit it points at; a lightweight tag shows the commit
   only), the registry page for a package.
4. **Check what already exists.** Before creating a tag, a release or a package version, look
   for it, and check its identity — which commit, which version — instead of recreating it. A
   tag that exists does not move by itself; never move, delete or recreate one to make the
   picture tidy. When it points somewhere unexpected, report that, and the decision it leaves
   to the user.
5. **No release expected?** Report only the merges and the validations you actually
   confirmed.

When an action fails after an earlier one succeeded, say what is done and what is not, and
stop. A retry, a revert or a cleanup is a new action and needs its own agreement.

## What this skill never does

- It never targets a branch other than `main`, and never falls back to one.
- It never merges every pull request, or publishes a release, on the strength of being
  invoked.
- It never stashes, discards, force-pushes, resolves a conflict or brings local commits into
  a pull request without a separate authorization.
- It never uses `--admin` to get past a protection.
- It never runs a publishing command to learn what it does, and never invents or installs a
  release mechanism.
- It never reports a queued merge as merged, or a merge, a tag and a published release as one
  thing.
- It never moves, deletes or recreates an existing tag or release.
