---
name: ship
description: Review open pull requests, check their English title and Nestor Task or Plan footer, and answer first with only the proposed action, such as which ones to merge into main, giving the readable details and each pull request's risk in words on request; then follow the repository's own release procedure. Run only after a direct user invocation, such as /nestor-beta:ship or $nestor-beta:ship; never invoke it autonomously. The optional list argument returns only the PR list in read-only mode. It needs Git, the GitHub CLI and the Nestor MCP server, and only targets main. Without list, every pull request edit, merge, tag, workflow run or publication waits for the user's agreement at that moment.
argument-hint: "[list]"
disable-model-invocation: true
---

# Ship

Turn "what is open on this repository" into a diagnosis, then a proposal, and — only once the
user agrees — into merges on `main`, followed by the release procedure the repository already
has. Git and the GitHub CLI (`gh`) do the work; the Nestor MCP server confirms the referenced
Nestor Tasks and Plans.

The user decides every action that cannot be undone. Your part is to make that decision easy
and safe: look at everything there is to see, propose one clear action, explain what you found
and what you could not see when the user asks, and ask when each action comes up rather than
once at the start.

## Identify the plugin version

Pass `{ "version_hash": "2ede0426ee06206cd" }` on every Nestor MCP call.

## Modes

`/nestor-beta:ship [list]` — Codex: `$nestor-beta:ship [list]`.

- **No mode argument:** run the existing diagnosis, proposal, agreed merges and repository
  release procedure below. The first response is the proposed action alone (level 1 in
  "Merge risk and report"); the details (level 2) come only when the user asks for them.
- **`list`:** `ship list` returns only the level 2 block of every open PR. Apply inventory and
  verification with the read-only substitutions below, then stop before sections 3–5. Do
  not propose merges or releases, ask for approval, or offer a next action. `list` is a mode,
  never a target branch; the target remains `main`.

In `list`, make only the reads needed for the blocks and their risk: GitHub queries, Nestor
reads and local inspection. Never mutate remote state or local files, refs, branches or
worktrees. Do not fetch, checkout, create/remove a worktree, write output files, run builds
or tests that could write artifacts, edit a pull request, merge, tag, launch workflows,
publish or deploy. Read existing CI results and logs instead; unperformed validation is a
stated coverage limit.

Read remote files needed to understand checks or changed workflow/release effects with
`gh api --method GET "repos/OWNER/REPO/contents/PATH?ref=SHA"`, decoding the returned content,
or `git show SHA:PATH` when the pinned object already exists locally. Do not fetch a missing
object. Keep unrelated release discovery out of this mode.

The response contains only those PR blocks, in the user's language and in the order of
level 2: no header, end of report, proposed action or question. Put unknown data in the
affected PR's State or Risk, in plain words, including local coverage limits and any title
or footer that does not conform; no separate inventory or progress narration. If there are
no open PRs, say only that. If the repository, authentication or `main` cannot be resolved,
give one concise error and stop without asking for an action.

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
   In normal mode, keep the count for the header of the details; in `list`, return every
   PR's block without a summary.
4. **Split them.** The pull requests whose base is `main` are the candidates. The others,
   whose base is another branch — often one that stacks on a candidate — are out of
   selection: the details still show them, with the base they target.
5. **Look at this machine.** In normal mode, `git worktree list --porcelain` lists the
   worktrees. For each reachable one, `git -C <path> status --porcelain=v1 --branch` shows uncommitted changes
   and `git -C <path> log --oneline HEAD --not --remotes` the commits that no remote branch
   contains yet, a detached worktree included. `git log --oneline --branches --not --remotes`
   covers the local branches checked out nowhere. Having no upstream does not make a branch
   unpushed, since its commits may already sit on another remote branch: these two are the
   test. When the details report it, keep it to one sentence: name the worktrees that hold
   uncommitted changes or unpushed commits, and count the clean ones instead of listing them.
   In `list`, use `git worktree list --porcelain` and inspect only local work relevant to the
   PR head repositories and branches, using
   `GIT_OPTIONAL_LOCKS=0 git -C <path> status --porcelain=v1 --branch` so status does not
   refresh the index. Use `git ls-remote <candidate-head-repository-url> refs/heads/BRANCH`
   for a live remote head, including a fork's own repository, and compare local history to
   that SHA only if its object is already present. Cached remote
   refs alone do not prove commits are unpushed. If comparison is unavailable, put local
   push state unknown in the affected PR's State; do not fetch to resolve it.

Keep this inventory for the report described in "Merge risk and report". In normal mode, the
first response is the proposed action alone (level 1). The count, the `main` baseline,
whether `main` is ahead of its latest release and the local work appear only in the details
(level 2), in plain words, or when the user asks. Local work on a candidate's branch goes
into that PR's State and, when it blocks, into the proposed action. In `list`, output only
the PR blocks. You see this machine's clones and worktrees and GitHub's state. You do not see
another agent's unsaved work, another machine, or a session that has not pushed; say so
where you report local work, instead of implying complete coverage.

## 2. Verify each pull request

For every open pull request, read the evidence that decides whether it can land on `main`
as it stands now. Only a candidate whose base is `main` can be ready; the others remain out
of selection, but their risk is assessed with the same meaning.

```bash
gh pr view N --repo OWNER/REPO --json number,title,url,body,isDraft,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,mergeable,mergeStateStatus,reviewDecision,latestReviews,reviewRequests,statusCheckRollup
gh pr checks N --repo OWNER/REPO
gh pr checks N --repo OWNER/REPO --required
gh pr diff N --repo OWNER/REPO
```

- **Pinned evidence.** Keep the full `headRefOid` and the full `main` baseline SHA with the
  evidence. Re-read the head, base and GitHub's `main` SHA before reporting. If either commit
  or the base changed, discard the old assessment, repeat the affected checks and assess the
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
  agrees; otherwise the requirement is unknown. Record which reviews were actually received
  and whether the required approvals apply to this head.
- **Dependencies between pull requests.** A base branch that is another pull request's head,
  a "depends on #N" in a description, two pull requests editing the same lines or bumping the
  same version: each one fixes an order, or means the later pull request needs attention once
  the earlier one has merged.
- **Work in progress.** Uncommitted changes or unpushed commits in a worktree matching the
  candidate's head repository and branch (`headRefName`) mean the remote head may not be what
  its author means to ship. Say so in that PR's State and, when it blocks the merge, ask
  about it in the proposed action.
- **The diff.** It is what lands on `main`. Read it for what the title does not say — a
  changed workflow or release file, anything that contradicts the description. A diff for
  another base does not establish integration with `main`; state that limit. Record relevant
  validations actually executed, with command, result and commit, separately from claims
  made in the PR body. A declared test result without inspected evidence stays unverified.

An unknown state, a required check that is absent or inconclusive, a missing required review,
or a conflict is never a green light.

### Title and Nestor footer

A pull request also has to say what it delivers and which Nestor Tasks or Plans it serves.
Check both on every open pull request, from the `title` and `body` read above.

**Title.** It is in English and carries no Nestor id or slug.

**Footer.** A pull request that contributes to Nestor Tasks or Plans ends its description
with one visible line, the last of the description:

```
nestor tasks: brown_turtle, gray_xerinae, copper_manatee
```

These are the referenced items' slugs, exactly as Nestor returns them, never ids; a comma
and a space separate them, and none appears twice.

**Project.** A slug is unique inside a project, not across the journal, so the items are
read in the Nestor project of this repository: the one named after it. Read it once with
`get_project`, passing the `REPO` of `OWNER/REPO` as `name`, and keep the id it returns for
the scope of every item read. When no project carries that exact name, the references stay
unverified: say so, and outside `list` ask which project the repository belongs to.

Then check four things:

- **Format.** The footer is one line, the last of the description, written exactly this way.
- **Existence.** Read the listed slugs with `get_item`, up to five per call in `ref`, with
  `scope: { mode: "project", projectId }` and a `known` array of the same length. At each
  position, send the matched `{ version, etag }` pair when the item's content is already
  held — another pull request lists the same item, or an earlier verification read it —
  and `null` only when that content is absent or incomplete. With `unchanged: true`, keep
  the held content and pair; a full answer replaces them. Every slug must resolve to one
  Task (`type: "task"`) or Plan (`type: "plan"`) of that project; any other item type makes
  the footer invalid.
- **Correspondence.** The diff actually contributes to each listed Task or Plan. For a
  Plan, verify a contribution to at least one code Task in its subtree, following `planId`
  and `parentPlanId`; read the tree or ancestry as needed. A partial contribution is enough:
  the footer links an item to the code, it does not declare the item or its subtree finished.
  A Task or Plan listed only as a dependency does not belong. Compare the diff with the
  items and subtree you read; never invent a correspondence from a resembling title.
- **Grouped deliveries.** A pull request that brings other pull requests or an intermediate
  branch into `main` keeps every slug their footers carried. Read the footers of the pull
  requests merged into its head branch that `main` does not hold yet, and name each slug
  that was lost.

A title that fails, or a footer that fails one of these checks, is non-conforming: the pull
request is blocked until it is corrected, whatever its risk. A missing or invalid
footer is not validated traceability. A missing footer alone does not block, since a pull
request may serve no Nestor Task or Plan; only the user can confirm that. Say it is missing
and never guess the references. When Nestor cannot be reached, the references stay
unverified: state that limit without treating it as a pass.

### Merge risk and report

Assess every open PR on two separate axes, from the evidence above. Neither one is a number,
internally or in the report.

- **State — can it merge into `main` now, at the examined head and baseline?** **Ready**,
  **blocked** or **out of selection**, as the gates above decide. A PR that is not ready
  keeps its cause and the action that would make it ready.
- **Risk — what would an error in this change cost?** **Low**: complete, favorable evidence
  on a targeted change. **Medium**: evidence absent or inconclusive — no CI, limited
  coverage, unknown rules on `main` or unknown mergeability. **High**: a broad or sensitive
  change — a workflow, a release, authentication, a data migration — with weak coverage, or
  a diff that contradicts its description. No CI is a coverage limit, not a failed check;
  local or optional checks you actually observed can supply the missing evidence. These are
  anchors, not a formula: weigh the evidence and give the reason in one sentence.

A low risk replaces no mandatory check, protection, group rule or user agreement. Groups —
ready, blocked, out of selection — come from the existing gates above, never from the risk.
Any head or `main` change invalidates the assessment; reassess after each merge and before
seeking renewed approval.

The report has two levels. Its examples are in English, like the rest of this skill, which
does not set the language of your replies: write all of it, the block heading and the reply
words included, in the user's language.

**Level 1 — the proposed action.** In normal mode, the first response is this block alone.
Every later proposal — a pull request edit, a merge, a release step — is the same block,
preceded only by the result of the previous action in one or two sentences with its useful
link:

```text
## ▶ PROPOSED ACTION

**Merge [#40](https://github.com/OWNER/REPO/pull/40) — scrolling Trending banner — into main**

Shall I do it? Reply "yes" or "details".
```

- **(a)** The bold line gives the verb, each pull request with its link and what it does in
  plain words, and the destination.
- **(b)** Several ready PRs make one grouped action, in the chosen order: "Merge #12 then
  #16 into main". A "yes" covers exactly that list and that order. Each PR is still verified
  again just before its merge (section 4), and a change found there stops the sequence.
- **(c)** When the merge method needs confirming, the line names it in plain words: "with a
  merge commit, like the previous PRs". A PR without a Nestor footer is named the same way,
  "though it names no Nestor Task or Plan", so that "yes" confirms it serves none.
- **(d)** A line starting with ⚠ appears only when the action automatically triggers a
  publication — a tag, a GitHub Release, a package, a version notification — or a
  deployment: "⚠ Publishes release v1.4.0". Otherwise there is no effect line.
- **(e)** When the next action is blocked, the block proposes the action that unblocks it,
  such as the exact correction of a PR footer, or names the decision it awaits, in one
  sentence.
- **(f)** When `main` is ahead of its latest release and no PR is left to merge, the
  proposed action is the release step.
- **(g)** When there is nothing to ship, one sentence says so, with no block and no question.

Level 1 shows no SHA, check name, GitHub state, count, `main` baseline or table, and names
local work only when it blocks the action.

**Level 2 — the details,** given when the user asks for them or for any explanation:

1. **Header.** One line: the repository and the number of PRs in each state.
2. **One block per PR.** Its title carries the link and says what the PR does in plain
   words, drawn from the diff and the Nestor items you read — never a word-for-word
   translation of its English title. Four lines follow: **What it changes**, the effect for
   the user or the product in one sentence; **State**, ready, blocked or out of selection,
   with the cause and the action needed when it is not ready; **Risk**, low, medium or high,
   with its reason in one sentence; **Task**, the Tasks or Plans of its footer, cited with
   Nestor's item citation rule, or the missing footer and the decision it needs.
3. **Order.** Ready PRs first, then blocked ones, then those out of selection.
4. **End.** **If I merge**: what the merges start — CI, a release, a deployment, or nothing
   published. **Next**: the step after them. Local work and how far `main` is ahead of its
   latest release, in one sentence when they matter. Then the same proposed action block.

SHAs, check names, GitHub states, protections and rulesets, 403 refusals and sources (file
and line) appear only when the user asks again, or when they block a PR, and then in plain
words.

The other level 1 cases. Two ready PRs, merged in the chosen order:

```text
## ▶ PROPOSED ACTION

**Merge [#12](https://github.com/OWNER/REPO/pull/12) — CSV export of the journal — then [#16](https://github.com/OWNER/REPO/pull/16) — installation guide in three steps — into main**

Shall I do it? Reply "yes" or "details".
```

A merge that publishes on its own, with a method to confirm:

```text
## ▶ PROPOSED ACTION

**Merge [#21](https://github.com/OWNER/REPO/pull/21) — offline mode — into main, with a merge commit like the previous PRs**

⚠ Publishes release v1.4.0

Shall I do it? Reply "yes" or "details".
```

A footer to correct before the merge:

```text
## ▶ PROPOSED ACTION

**Remove `gray_xerinae`, which Nestor does not know, from the footer of [#18](https://github.com/OWNER/REPO/pull/18) — automatic retry of failed uploads**

Shall I do it? Reply "yes" or "details".
```

A decision only the user can make, still in one sentence:

```text
## ▶ PROPOSED ACTION

**Tell me which Nestor project holds this repository: none is named REPO, so no pull request footer can be checked**

Reply with the project's name, or "details".
```

A release step, with no PR left to merge:

```text
## ▶ PROPOSED ACTION

**Release v1.4.0 from main by pushing its tag — it ships the three changes merged since v1.3.2**

⚠ Publishes release v1.4.0 on GitHub and npm

Shall I do it? Reply "yes" or "details".
```

Nothing to ship:

```text
Nothing to ship: no pull request is open, and main matches its latest release.
```

Level 2, once the user asks for details:

```text
REPO: 2 PRs ready to merge, 3 blocked, 1 out of selection

**[#12](https://github.com/OWNER/REPO/pull/12) — Export the journal as a CSV file**
- What it changes: users can download all their entries as a spreadsheet.
- State: ready. The tests pass and nothing conflicts with main.
- Risk: low. A targeted change: 120 lines of code and 300 lines of tests.
- Task: `brown_turtle (CSV export)`

**[#16](https://github.com/OWNER/REPO/pull/16) — Rewrite the installation guide in three steps**
- What it changes: new users can install the app without reading one long paragraph.
- State: ready. Nothing blocks it.
- Risk: medium. No automated check runs on documentation, so only a reading of the diff supports it.
- Task: `olive_wren (installation guide)`

**[#18](https://github.com/OWNER/REPO/pull/18) — Retry failed uploads automatically**
- What it changes: an upload cut off by the network resumes by itself instead of failing.
- State: blocked. The code is ready, but its footer names `gray_xerinae`, which Nestor does not know: remove it before merging.
- Risk: low. Tests cover the retry, and the change stays inside the upload module.
- Task: `copper_manatee (upload retry)`; `gray_xerinae` is unknown.

**[#14](https://github.com/OWNER/REPO/pull/14) — Switch sign-in to company accounts**
- What it changes: users would sign in with their company account instead of a password.
- State: blocked. It conflicts with recent changes on main, and a required test run fails: its author has to update the branch and fix the tests.
- Risk: high. It changes authentication, and its tests fail.
- Task: `teal_heron (single sign-on)`

**[#17](https://github.com/OWNER/REPO/pull/17) — Refresh stale search results**
- What it changes: search results update as soon as an entry changes.
- State: blocked. GitHub refuses to show this account the rules that protect main, so what the PR still needs is unknown: a repository admin has to share them or grant read access.
- Risk: medium. The rules for merging into main are unknown.
- Task: `amber_lynx (search cache)`

**[#15](https://github.com/OWNER/REPO/pull/15) — Document the CSV export**
- What it changes: the user guide explains the export that #12 adds.
- State: out of selection. It targets the `feature/export` branch, not main, and needs #12 first.
- Risk: medium. Its diff was made against another branch, so how it would land on main is unknown.
- Task: `brown_turtle (CSV export)`

If I merge: the tests run again on main; nothing is published or deployed.

Next: releasing these changes, since main will then be ahead of its latest release, v1.3.2.

Local work: two commits in the `docs-draft` worktree are on no remote branch yet.

## ▶ PROPOSED ACTION

**Merge [#12](https://github.com/OWNER/REPO/pull/12) — CSV export of the journal — then [#16](https://github.com/OWNER/REPO/pull/16) — installation guide in three steps — into main**

Shall I do it? Reply "yes" or "details".
```

Do not stash, discard, force-push, resolve a conflict, or bring local commits into a pull
request without a separate authorization. In normal mode, when a check needs a checkout,
use a clean temporary worktree at the examined head outside the user's working tree, and
remove it afterwards. In `list`, use observed CI/log evidence without a checkout or local
validation run, count missing coverage in the risk, output the PR blocks and **stop**.

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

**How to conclude.** Keep the file and line behind each conclusion
(`git show <ref>:<path> | nl -ba` shows the numbers), and give them when the user asks. A
procedure you cannot establish stays uncertain. Never run a publishing command to find out
what it does.

Then act on the procedure you found:

- **It publishes automatically after a merge into `main`.** Announce the effect on the ⚠
  line of the proposed action, before the user agrees; after the merge, follow the workflow
  and check what it did. Read its conditions: a release workflow on `main` does not mean
  every merge publishes — filters, `if` conditions and version guards decide.
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

**Notes built from pull request descriptions.** Whatever triggers it, a procedure that reuses
those descriptions in what it publishes must leave the `nestor tasks:` footer out. Check
here, in the chain you just read, that it drops that line. When it does not, a merge or a
release that publishes on its own carries the footer out before anyone can remove it: the
proposed action is the correction the procedure needs; trigger no merge or release
that would publish the footer until that correction is agreed and in place. The correction
is to the procedure, never to the pull request: the footer stays in the description, where
it is the only link to the tasks. Filtering you cannot establish leaves the procedure
uncertain.

## 4. Propose, then merge

**The proposal.** It is the level 1 block of "Merge risk and report": the selected pull
requests in the merge order, the merge method when it needs confirming, and the ⚠ line for
any automatic effect a merge will have according to the release procedure you found. The
repository, `main` with its baseline commit, the head commits you verified, the validations
done and the reason for the order stay internal, pinned with the evidence, and are given when
the user asks. Then wait for the user's agreement, unless one already given in the session
covers exactly this.

The method is the one the repository allows and documents: its merge settings
(`gh api repos/OWNER/REPO --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'`),
the rules on `main`
(`gh api --paginate "repos/OWNER/REPO/rules/branches/main?per_page=100"` can restrict methods), and
its contributor documents. When several are allowed and none is documented, do not settle it
yourself: the action line names the method you propose in plain words, as rule (c)
describes, so that the user's agreement decides it.

**Titles and footers.** Have non-conforming metadata corrected before the merge: the proposed
action is then the exact correction each failing title or footer needs, using only slugs you
verified. For a missing footer, ask whether the pull request serves Nestor Tasks or Plans,
and which ones, through the action line, as rule (c) describes.
Editing a pull request is a write of its own — `gh pr edit N --repo OWNER/REPO --title … --body-file …`
— so it waits for its agreement, and the pull request is verified again afterwards.

**The merges.** For each pull request, in the agreed order:

1. Read it again. Its base must still be `main` and its head the commit you verified, and its
   checks, reviews and mergeability must still hold. Read `main`'s current SHA too and
   reassess the evidence, state and risk if that baseline moved. The merge below guards the head,
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
delivered state in one or two sentences: what merged, with its link, what did not and why;
the commits are given when the user asks. What remains goes back through a proposed action
and needs a new agreement.

## 5. Finish

Report each result — merged, pending, failed, release published — in one or two sentences
with its useful link, then the next proposed action block if one remains.

1. **Check `main`.** Fetch `REMOTE`, then take the final commit of `main` and look at its runs:
   `gh run list --repo OWNER/REPO --commit <sha> --json databaseId,name,status,conclusion,event,url`.
   A workflow takes a moment to start, so read again when nothing shows yet. Wait for the ones
   the merge was expected to start with `gh run watch <id> --repo OWNER/REPO --exit-status`,
   and report each result as it is.
2. **Prepare the release, when the procedure needs an action from you or the user** — a tag,
   a manual workflow, a documented command. Prepare a concrete proposal before asking: the
   version and the tag, the commit, the notes, any assets, and the command exactly as the
   repository documents it. Propose it as the level 1 block, the release in the action line
   and what it publishes on the ⚠ line; give the commit, the notes, the assets and the command
   when the user asks. Notes that reuse pull request descriptions leave their `nestor tasks:`
   footer out. When the procedure needs edits first — a version bump, a changelog, a release
   pull request — prepare them here and show them when the user asks; opening or pushing them
   is an action that needs its own agreement. Never create a tag that disagrees
   with the versions the repository declares. `gh release create <tag> --repo OWNER/REPO`
   creates the tag itself when it does not exist, so add `--verify-tag` when the tag is meant
   to exist already.
3. **Follow what was triggered.** Watch the workflows the merge or the tag started, then
   confirm the commit, the tag and the URL of the release or package, according to the effect
   you announced:
   `gh release view <tag> --repo OWNER/REPO --json url,tagName,targetCommitish,isDraft` for a
   GitHub Release, `git ls-remote --tags REMOTE <tag> '<tag>^{}'` for a tag (an annotated tag
   shows its own object, then the commit it points at; a lightweight tag shows the commit
   only), the registry page for a package. Confirm too that the published notes carry no
   `nestor tasks:` footer, and report one that got through.
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
  included, runs merge/release steps or asks for approval; only the PR blocks are returned.
- It never merges every pull request, or publishes a release, on the strength of being
  invoked.
- It never merges a pull request whose title or Nestor footer is non-conforming, and never
  guesses the Tasks or Plans a pull request serves.
- It never puts a `nestor tasks:` footer in the release notes it prepares, and never triggers
  a merge or a release that would publish one.
- It never stashes, discards, force-pushes, resolves a conflict or brings local commits into
  a pull request without a separate authorization.
- It never uses `--admin` to get past a protection.
- It never runs a publishing command to learn what it does, and never invents or installs a
  release mechanism.
- It never reports a queued merge as merged, or a merge, a tag and a published release as one
  thing.
- It never moves, deletes or recreates an existing tag or release.
