---
name: ship
description: Review open pull requests with a merge confidence percentage, check their English title and Nestor task footer, propose which ones to merge into main, then follow the repository's own release procedure. Run only after a direct user invocation, such as /nestor-beta:ship or $nestor-beta:ship; never invoke it autonomously. The optional list argument returns only the PR list in read-only mode. It needs Git, the GitHub CLI and the Nestor MCP server, and only targets main. Without list, every pull request edit, merge, tag, workflow run or publication waits for the user's agreement at that moment.
argument-hint: "[list]"
disable-model-invocation: true
---

# Ship

Turn "what is open on this repository" into a diagnosis, then a proposal, and — only once the
user agrees — into merges on `main`, followed by the release procedure the repository already
has. Git and the GitHub CLI (`gh`) do the work; the Nestor MCP server confirms the tasks a
pull request references.

The user decides every action that cannot be undone. Your part is to make that decision easy
and safe: look at everything there is to see, say what you found and what you could not see,
and ask when each action comes up rather than once at the start.

## Identify the plugin version

Pass `{ "version_hash": "282a6866cadd70f62" }` on every Nestor MCP call.

## Modes

`/nestor-beta:ship [list]` — Codex: `$nestor-beta:ship [list]`.

- **No mode argument:** run the existing diagnosis, proposal, agreed merges and repository
  release procedure below.
- **`list`:** `ship list` returns only the scored list of every open PR. Apply inventory and
  verification with the read-only substitutions below, then stop before sections 3–5. Do
  not propose merges or releases, ask for approval, or offer a next action. `list` is a mode,
  never a target branch; the target remains `main`.

In `list`, make only the reads needed for the list and its scores: GitHub queries, Nestor
reads and local inspection. Never mutate remote state or local files, refs, branches or
worktrees. Do not fetch, checkout, create/remove a worktree, write output files, run builds
or tests that could write artifacts, edit a pull request, merge, tag, launch workflows,
publish or deploy. Read existing CI results and logs instead; unperformed validation is a
stated coverage limit.

Read remote files needed to understand checks or changed workflow/release effects with
`gh api --method GET "repos/OWNER/REPO/contents/PATH?ref=SHA"`, decoding the returned content,
or `git show SHA:PATH` when the pinned object already exists locally. Do not fetch a missing
object. Keep unrelated release discovery out of this mode.

The response contains only PR rows or lines in the user's language: percentage first, link
and title, examined head and `main` baseline, base, group, concise evidence and useful limits.
Put unknown data in the affected PR's reason, including local coverage limits and any title
or footer that does not conform; no separate inventory, progress narration, proposal or
approval question. If there are no open PRs, say only that. If the repository,
authentication or `main` cannot be resolved, give one concise error and stop without asking
for an action.

## Scope and consent

- **The target is `main`, and only `main`.** The optional `list` argument selects a mode. The
  skill never asks which branch to ship to; other text written after its name remains the
  user's message, not a target. When `main` does not exist on the remote, explain the blocker
  and stop. Never fall back to another branch.
- **Without `list`, an invocation prepares a diagnosis and a proposal.** It is not agreement to
  merge every pull request, and not agreement to publish a release. Ask at the moment of each
  action that changes something beyond this machine: a pull request edit, a merge, a tag
  push, a workflow run, a script run, a release creation. An agreement already given in the
  session holds for its exact scope — those pull requests, those head commits, that action —
  and for nothing wider.
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
   no command depends on an implicit default. Keep the remote whose URL points at it as well —
   `REMOTE` below, often `origin` but not always — and use it wherever a `git` command names a
   remote: in a fork's clone, `origin` is usually the fork, and its `main` and its tags answer
   for the wrong repository. A fork, or remotes that point at different repositories, leave
   the target ambiguous: name the candidates and ask in normal mode; in `list`, report the
   ambiguity and stop. When this is not a GitHub repository, no remote points at it, or `gh`
   is not authenticated, say so and stop.
2. **Read the remote state.** In normal mode, run `git fetch --prune REMOTE`, then confirm
   `main` as a remote-tracking branch with `git rev-parse --verify refs/remotes/REMOTE/main`.
   In both modes, read GitHub's current `main` with
   `gh api repos/OWNER/REPO/branches/main --jq .commit.sha` and record its full SHA as the
   baseline. In normal mode, the fetched SHA must match it; refresh again if they differ.
   In `list`, do not fetch or require a local remote-tracking ref: GitHub's SHA is the
   baseline. If `main` is absent, that is the blocker described in "Scope and consent".
3. **Read every open pull request.** `gh pr list` returns 30 results by default and does not
   say when it stops, so walk every page:
   `gh api --paginate "repos/OWNER/REPO/pulls?state=open&per_page=100" --jq '.[] | [.number, .base.ref, .draft, .head.sha[0:7], .title] | @tsv'`.
   In normal mode, state how many you read; in `list`, return every row without a summary.
4. **Split them.** The pull requests whose base is `main` are the candidates. The others,
   whose base is another branch — often one that stacks on a candidate — are out of
   selection: list them anyway, with the base they target.
5. **Look at this machine.** In normal mode, `git worktree list --porcelain` lists the
   worktrees. For each reachable one, `git -C <path> status --porcelain=v1 --branch` shows uncommitted changes
   and `git -C <path> log --oneline HEAD --not --remotes` the commits that no remote branch
   contains yet, a detached worktree included. `git log --oneline --branches --not --remotes`
   covers the local branches checked out nowhere. Having no upstream does not make a branch
   unpushed, since its commits may already sit on another remote branch: these two are the
   test. Keep the summary short: name the worktrees that hold uncommitted changes or unpushed
   commits, and count the clean ones instead of listing them.
   In `list`, use `git worktree list --porcelain` and inspect only local work relevant to the
   PR head repositories and branches, using
   `GIT_OPTIONAL_LOCKS=0 git -C <path> status --porcelain=v1 --branch` so status does not
   refresh the index. Use `git ls-remote <candidate-head-repository-url> refs/heads/BRANCH`
   for a live remote head, including a fork's own repository, and compare local history to
   that SHA only if its object is already present. Cached remote
   refs alone do not prove commits are unpushed. If comparison is unavailable, put local
   push state unknown in the affected row; do not fetch to resolve it.

Keep this inventory for the scored report below. Lead the normal diagnosis with that report,
then give the count, the baseline and a short local-work summary. In `list`, output only the
scored report. You see this machine's clones and worktrees and GitHub's state. You do not see
another agent's unsaved work, another machine, or a session that has not pushed; say so
instead of implying complete coverage.

## 2. Verify each pull request

For every open pull request, read the evidence that decides whether it can land on `main`
as it stands now. Only a candidate whose base is `main` can be ready; the others remain out
of selection, but still receive a score with the same meaning.

```bash
gh pr view N --repo OWNER/REPO --json number,title,url,body,isDraft,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,mergeable,mergeStateStatus,reviewDecision,latestReviews,reviewRequests,statusCheckRollup
gh pr checks N --repo OWNER/REPO
gh pr checks N --repo OWNER/REPO --required
gh pr diff N --repo OWNER/REPO
```

- **Pinned evidence.** Keep the full `headRefOid` and the full `main` baseline SHA with the
  evidence. Re-read the head, base and GitHub's `main` SHA before reporting. If either commit
  or the base changed, discard the old assessment, repeat the affected checks and score the
  new pair. A diff or a check read during that change does not belong to a stable assessment.
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
  `main` requires is also in its classic protection,
  `gh api repos/OWNER/REPO/branches/main/protection`, and in its rulesets,
  `gh api --paginate "repos/OWNER/REPO/rules/branches/main?per_page=100"`; read the two
  separately, including every rule page. A partial or truncated response leaves requirements
  incomplete and must be reported as unknown. A 404 whose message is `Branch not protected`
  is an answer, not a refusal: `main` has no classic protection, and
  its rulesets still decide. Any other refusal (403, 404) means unknown, not none. Every
  required check must have concluded successfully **on the current head commit**
  (`headRefOid`) — a run on an earlier head does not count. Pending, failed, cancelled,
  skipped or missing is not green, and a required check that never ran is the quiet one.
  If the rollup does not establish a check's SHA, read its run details or the check-runs and
  status APIs for the pinned head before calling it passed. Distinguish **no CI configured**
  (confirmed from the configuration and the observed runs), **no checks required** (optional
  checks may still supply evidence), **a required check missing/pending/failed**, and
  **requirements unknown**. An empty check list alone proves neither no CI nor no rules.
- **Reviews.** `reviewDecision` `CHANGES_REQUESTED` or `REVIEW_REQUIRED` is blocked. An empty
  value establishes no review requirement only when the protection and ruleset evidence
  agrees; otherwise the requirement is unknown. Say which reviews were actually received
  and whether the required approvals apply to this head.
- **Dependencies between pull requests.** A base branch that is another pull request's head,
  a "depends on #N" in a description, two pull requests editing the same lines or bumping the
  same version: each one fixes an order, or means the later pull request needs attention once
  the earlier one has merged.
- **Work in progress.** Uncommitted changes or unpushed commits in a worktree matching the
  candidate's head repository and branch (`headRefName`) mean the remote head may not be what
  its author means to ship. Say so in its reason, and ask about it in the proposal.
- **The diff.** It is what lands on `main`. Read it for what the title does not say — a
  changed workflow or release file, anything that contradicts the description. A diff for
  another base does not establish integration with `main`; state that limit. Record relevant
  validations actually executed, with command, result and commit, separately from claims
  made in the PR body. A declared test result without inspected evidence stays unverified.

An unknown state, a required check that is absent or inconclusive, a missing required review,
or a conflict is never a green light.

### Title and Nestor footer

A pull request also has to say what it delivers and which Nestor tasks it serves. Check
both on every open pull request, from the `title` and `body` read above.

**Title.** It is in English and carries no Nestor id or slug.

**Footer.** A pull request that contributes to Nestor tasks ends its description with one
visible line, the last of the description:

```
nestor tasks: Xh23, DJ87, HDQZKJ9
```

These are the exact ids Nestor returned, whatever their length, never slugs; a comma and a
space separate them, and none appears twice. Check four things:

- **Format.** One such line, last in the description, written exactly this way.
- **Existence.** Read the listed ids with `get_item`, up to five per call in `ref`, with
  `scope: { mode: "global" }` and `null` for each in `known`. Every id must resolve to one
  task.
- **Correspondence.** The diff actually contributes to each listed task, the subtasks
  concerned included. A partial contribution is enough: the footer links a task to the
  code, it does not declare the task finished. A task that is only mentioned as a
  dependency does not belong in the list. Decide from the task you read and from the diff;
  never invent a correspondence from a resembling title.
- **Grouped deliveries.** A pull request that brings other pull requests or an intermediate
  branch into `main` keeps every id their footers carried. Read the footers of the pull
  requests merged into its head branch that `main` does not hold yet, and name each id
  that was lost.

A title or footer that fails a check is non-conforming: the pull request is blocked until it
is corrected, whatever its percentage. A missing or invalid footer is not validated
traceability. When the footer is missing, say so and do not guess the tasks: only the user
can confirm that a pull request serves no Nestor task. When Nestor cannot be reached, the
tasks stay unverified, which is a limit to state, not a pass.

### Merge confidence and report

Give every open PR an integer percentage from 0 to 100: confidence that **this PR can merge
into `main` at the examined head and baseline, with acceptable technical risk within the
checks performed**. One meaning serves **ready**, **blocked** and **out of selection**. It
does not measure confidence in the grouping, and it is not a statistically calibrated
probability. The facts are objective; their weighting and the remaining risk are judgment.

Use these indicative anchors, adapted to merge readiness rather than doctor's delivery
thresholds; do not turn them into a points formula or a new merge gate:

- **95–99%: complete favorable evidence.** Base `main`, non-draft, `MERGEABLE` and `CLEAN`;
  applicable protections and rulesets known; required checks and reviews satisfied or
  confirmed not required; diff read and relevant validations observed on this head;
  dependencies, overlaps, local work and workflow/release effects accounted for.
- **0–10%: a confirmed obstacle as the PR stands.** A conflict, failed required check,
  missing required approval, draft or different base prevents it landing on `main` now.
  Identify the obstacle even when other evidence is favorable.
- **20–60%: evidence absent or inconclusive.** Unavailable requirements, unknown mergeability
  or limited validation coverage leave material uncertainty. No CI is a coverage limit,
  not a failed check; actual local or optional checks may improve the assessment. A 403 is
  unknown requirements, not absent rules or a confirmed check failure.

Within these anchors, weigh the evidence and explain the remaining judgment briefly. A high
score replaces no mandatory check, protection, group rule or user agreement. Groups are
decided by the existing gates above, never by a percentage threshold. Any head or `main`
change invalidates the score; reassess after each merge and before seeking renewed approval.

Start every PR line with `85% - [#N Title](URL) — head SHA — main SHA — base — group — evidence
and limits`. In a table, put the percentage first, before the PR. Lead with the scored list,
in the user's language. Give concise observed facts, name missing or unknown evidence, and
make clear that the percentage is the residual judgment. These examples share the examined
`main` baseline `b012345`; abbreviated SHAs are for display only:

| Confidence (estimate) | Pull request | Head / main | Base | Group | Evidence and limits |
|---|---|---|---|---|---|
| 97% | [#12 Add export](https://github.com/OWNER/REPO/pull/12) | `a1b2c3d` / `b012345` | `main` | ready | observed: non-draft, MERGEABLE/CLEAN, rules known, required checks passed and approvals satisfied on this head, diff and relevant tests verified, dependencies and release effects understood, title and footer conform; judgment: broad coverage, residual risk beyond tests |
| 96% | [#18 Add retry](https://github.com/OWNER/REPO/pull/18) | `a9b8c7d` / `b012345` | `main` | blocked | observed: non-draft, MERGEABLE/CLEAN, required checks passed on this head, diff read; footer lists `DJ87`, which Nestor does not know; judgment: technically ready, blocked until the footer is corrected |
| 5% | [#14 Rework auth](https://github.com/OWNER/REPO/pull/14) | `e4f5a6b` / `b012345` | `main` | blocked | observed: conflict and required `validate` failed on this head; judgment: cannot land as-is |
| 60% | [#16 Update docs](https://github.com/OWNER/REPO/pull/16) | `d8e9f01` / `b012345` | `main` | ready | observed: non-draft, MERGEABLE/CLEAN, no required checks or reviews, no CI configured, diff read, no Nestor footer; unknown: automated validation coverage, tasks served; judgment: limited change, limited evidence |
| 35% | [#17 Fix cache](https://github.com/OWNER/REPO/pull/17) | `f1a2b3c` / `b012345` | `main` | blocked | observed: MERGEABLE/CLEAN; unknown: protections and rulesets returned 403, no displayed checks; judgment: requirements cannot be established |
| 10% | [#15 Docs on #12](https://github.com/OWNER/REPO/pull/15) | `c7d8e9f` / `b012345` | `feature/export` | out of selection | observed: different base, depends on #12; unknown: integration with main; judgment: cannot land on main as-is |

Do not stash, discard, force-push, resolve a conflict, or bring local commits into a pull
request without a separate authorization. In normal mode, when a check needs a checkout,
use a clean temporary worktree at the examined head outside the user's working tree, and
remove it afterwards. In `list`, use observed CI/log evidence without a checkout or local
validation run, record missing coverage in the score, output the scored report and **stop**.

## 3. Recognize the release procedure — before any merge

Do this before proposing a merge, because a merge may itself start a release, and the user has
to hear that before agreeing.

**Where to look.** The repository's agent and contributor files (`AGENTS.md`, `CLAUDE.md`,
`CONTRIBUTING.md`), `README.md`, the scripts in `package.json` and `Makefile`, and any
publishing configuration. Then `.github/workflows/*.yml` and `*.yaml`, read where they will
act: on the remote `main` (`git show REMOTE/main:<path>`), and, for every workflow or release
file a selected pull request adds, edits or deletes, in that pull request
(`git fetch REMOTE pull/N/head`, then `git show <headRefOid>:<path>`) — once it merges, that
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
  reach.** Report the uncertainty and the decision that is missing, and publish nothing on a
  guess. Do not invent a release mechanism or install one.

## 4. Propose, then merge

**The proposal.** Put in front of the user the repository, `main` with its baseline commit, the
selected pull requests with the head commits you verified, the merge order and why, the
validations done, the merge method, and the automatic effects each merge will have according
to the release procedure you found. Then wait for the user's agreement, unless one already
given in the session covers exactly this.

The method is the one the repository allows and documents: its merge settings
(`gh api repos/OWNER/REPO --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'`),
the rules on `main`
(`gh api --paginate "repos/OWNER/REPO/rules/branches/main?per_page=100"` can restrict methods), and
its contributor documents. When several are allowed and none is documented, ask in the
proposal instead of choosing.

**Titles and footers.** Have non-conforming metadata corrected before the merge. Name each
title or footer that fails and the correction it needs, using only ids you verified; for a
missing footer, ask whether the pull request serves Nestor tasks, and which ones. Editing a
pull request is a write of its own — `gh pr edit N --repo OWNER/REPO --title … --body-file …`
— so it waits for its agreement, and the pull request is verified again afterwards.

**The merges.** For each pull request, in the agreed order:

1. Read it again. Its base must still be `main` and its head the commit you verified, and its
   checks, reviews and mergeability must still hold. Read `main`'s current SHA too and
   reassess the evidence and score if that baseline moved. The merge below guards the head,
   not the base: a pull request retargeted to another branch keeps its head and would merge
   there. It does not guard the title or the description either: read both again, and when
   one changed since you checked it, check it again before merging, even though the code is
   the same.
2. Merge it locked on that commit:
   `gh pr merge N --repo OWNER/REPO --match-head-commit <headRefOid> --<method>`, where the
   method is `merge`, `squash` or `rebase`. GitHub refuses the merge if the branch moved since
   you verified it, so what lands is exactly what was examined.
3. Confirm the result:
   `gh pr view N --repo OWNER/REPO --json state,mergedAt,mergeCommit,baseRefName,autoMergeRequest`.
   Auto-merge and a merge queue only record a request. Wait for the real outcome before
   reporting a merge, and before starting the next one; a request still pending after a
   reasonable wait is reported as pending, not as merged.
4. Verify the remaining pull requests again, as in "Verify each pull request": `main` just
   moved, so one of them may now conflict, be behind, or have new checks running.

Respect GitHub's protections. Never use `--admin` to get around one; when a protection blocks
a merge, report it. Stop when the approved scope changes — a head commit moved, a base
changed, the user changed the list — or a new verification fails, and report the partly
delivered state: what merged and at which commit, what did not and why. What remains goes
back through a proposal and needs a new agreement.

## 5. Finish

1. **Check `main`.** Fetch `REMOTE`, then take the final commit of `main` and look at its runs:
   `gh run list --repo OWNER/REPO --commit <sha> --json databaseId,name,status,conclusion,event,url`.
   A workflow takes a moment to start, so read again when nothing shows yet. Wait for the ones
   the merge was expected to start with `gh run watch <id> --repo OWNER/REPO --exit-status`,
   and report each result as it is.
2. **Prepare the release, when the procedure needs an action from you or the user** — a tag,
   a manual workflow, a documented command. Put a concrete proposal in front of the user
   before asking: the version and the tag, the commit, the notes, any assets, and the command
   exactly as the repository documents it. Notes that reuse pull request descriptions leave
   their `nestor tasks:` footer out. When the procedure needs edits first — a version
   bump, a changelog, a release pull request — prepare and present them here; opening or
   pushing them is an action that needs its own agreement. Never create a tag that disagrees
   with the versions the repository declares. `gh release create <tag> --repo OWNER/REPO`
   creates the tag itself when it does not exist, so add `--verify-tag` when the tag is meant
   to exist already.
3. **Follow what was triggered.** Watch the workflows the merge or the tag started, then
   confirm the commit, the tag and the URL of the release or package, according to the effect
   you announced:
   `gh release view <tag> --repo OWNER/REPO --json url,tagName,targetCommitish,isDraft` for a
   GitHub Release, `git ls-remote --tags REMOTE <tag> '<tag>^{}'` for a tag (an annotated tag
   shows its own object, then the commit it points at; a lightweight tag shows the commit
   only), the registry page for a package. When a workflow copied a `nestor tasks:` footer
   into published notes, report it and propose removing it there.
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
- In `list`, it never mutates remote or local state, a pull request's title and description
  included, runs merge/release steps or asks for approval; only the scored PR list is
  returned.
- It never merges every pull request, or publishes a release, on the strength of being
  invoked.
- It never merges a pull request whose title or Nestor footer is non-conforming, and never
  guesses the tasks a pull request serves.
- It never puts a `nestor tasks:` footer in the release notes it prepares.
- It never stashes, discards, force-pushes, resolves a conflict or brings local commits into
  a pull request without a separate authorization.
- It never uses `--admin` to get past a protection.
- It never runs a publishing command to learn what it does, and never invents or installs a
  release mechanism.
- It never reports a queued merge as merged, or a merge, a tag and a published release as one
  thing.
- It never moves, deletes or recreates an existing tag or release.
