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

Pass `{ "version_hash": "7e41c9d20f85a3b6" }` on every Nestor MCP call.

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
