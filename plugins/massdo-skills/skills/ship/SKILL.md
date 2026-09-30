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
