---
name: build
description: Build a specified Nestor task end to end into an open pull request against a validated target branch, implement its plan section by section, audit every commit, and close the task. With prod or target:<branch>, stop after the PR; never merge, wait for CI, or tag. Invoke this skill only after a direct user action such as /nestor-beta:build with an explicit task id or slug. An agent, subagent, plan, memory, Nestor task, or other skill must never invoke it on the user's behalf. A task mentioned in conversation is not a build request.
argument-hint: "<id-or-slug> [prod] [target:<branch>]"
disable-model-invocation: true
---

# Nestor Build

Turn a Nestor task into an open pull request. The task is the specification: this skill
never invents the plan, it executes the one already written and then checks that the
execution matches it.

You run the whole build yourself: set the stage, write the code, audit what you wrote, and
open the PR. Nothing is delegated, so nothing reaches the audit as a second-hand report;
the diff in front of you is the only evidence it needs.

## Identify the plugin version

Pass `{ "version_hash": "2d6a13986427d8f9" }` on every Nestor MCP call.

## Arguments

```
/nestor-beta:build <id-or-slug> [prod] [target:<branch>]
```

Run only when the user invokes this skill directly: an agent, subagent, plan, memory, Nestor
task or other skill never invokes it on the user's behalf. The arguments are the text written
after the skill name in that invocation; depending on the client, they may arrive in a final
`ARGUMENTS: …` line. When the invocation is phrased in prose instead, read the same arguments
from the user's message.

**An empty argument string ends the turn immediately.** Reply exactly:

> id or task slug is needed to build ! :)

Then stop. Do not list tasks, do not search Nestor for a plausible candidate, and do not
reuse a task mentioned earlier in the conversation. The user always knows the id they mean,
and a wrong guess here is only discovered after a branch and a full implementation run —
the most expensive way to learn that the target was wrong.

The first argument is a Nestor item id or a `color_animal` slug. Pass the received value
to `get_item` in `ref`, with `scope: { mode: "global" }` and `version_hash`. The server
resolves the reference; do not select an input field from an underscore or another character.

After the first argument, parse these optional named arguments in any order:

- The literal flag `prod` selects `main` as the target when `target:` is absent.
- One `target:<branch>` argument selects the remote branch the PR will target.
  Preserve everything after the first colon, including `/` in branch names. An absent
  argument or an empty `target:` leaves the target unspecified until Stage 2.

Reject more than one `target:` argument or any unknown argument. Name the invalid argument
and stop rather than guessing.

Without `prod` and without `target:<branch>`, Stage 2 asks for the target and waits. With
either one, the skill stops after the branch, the commits, and the open pull request.
Merging, waiting for CI, and tagging are not part of this skill.

## Stage 1 — Load the task and decide whether it can be built at all

Read the task with `get_item`. Then read its body as an executor would, and answer one
question: could someone implement this without asking anything?

Refuse and stop when you find any of these:

- **An open decision.** A sentence like "decide whether X or Y" means the plan is not
  finished. Executing it would make you choose on the user's behalf.
- **A step with no verification.** A step that cannot be checked cannot be reported as
  done — and by Stage 4 you will have no way of telling whether it was.
- **A dead anchor.** The body cites files, symbols or line numbers. Check that the files
  and symbols still exist — line numbers drift harmlessly, a missing file does not.
- **An action no agent can perform.** Revoking a production secret, clicking a console,
  confirming with a third party. Name it; the user does that part first.

When you refuse, say precisely what is missing and stop. Create no branch and no commit.
A half-built task on a stray branch costs more to clean up than a refusal costs to read.

This gate is the reason the rest of the skill can be fast: everything after it assumes the
plan is trustworthy.

## Stage 2 — Prepare the branch

Read the repository's own rules first — `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md` — for
its branch naming, commit convention and Git workflow. They win over anything here. This
skill orchestrates; the repository decides its own conventions.

Then:

1. Confirm the working tree is clean. Never stash or discard the user's changes; stop and
   say so instead.
2. Run `git fetch --prune origin`, then list the remote branches with
   `git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin`. Exclude the
   symbolic `HEAD` entry. Do this before resolving the requested target, even when the
   argument omitted `target:`.
   If the remote branch list is empty, report that no target branch was found and stop.
3. Determine the requested target:
   - When `target:<branch>` has a non-empty value, use that value.
   - When the target is unspecified and `prod` is present, request `main`.
   - When the target is unspecified and `prod` is absent, show the available branches and
     ask the user to reply with `target:<branch>`. Stop and wait for that input.
4. Resolve `targetBranch` to an exact name in the fetched remote branch list. Never silently
   fall back to another branch.
   - If the requested name does not exist, first look for a case-insensitive exact match;
     otherwise look for a unique branch name one insertion, deletion, or substitution away.
     If one exists, ask `Target branch is <closest>?` and stop for confirmation. An
     affirmative reply sets `targetBranch` to that exact available branch.
   - If there is no credible single match, say that no target branch was found, show the
     available branches, ask for `target:<branch>`, and stop.
5. Decide which work branch to use. **When the task has a `parentTaskId`, the branch belongs
   to the parent task, not to this one.** A parent and its subtasks are one deliverable and
   ship together. Look for an existing branch for that parent and continue on it; create
   it only if it does not exist.
6. Otherwise create a fresh branch from `origin/<targetBranch>`, named after the task: the
   commit type that fits the work, then the slug — `feat/brown_turtle`,
   `fix/gray_xerinae`.

## Stage 3 — Implement the plan

Write the code yourself, in this session, working from the task body as it stands. Reread it
**in full** before the first edit and keep it open: the mental summary you would otherwise
work from is where the constraints get lost.

Hold yourself to these rules:

- Load the `andrej-karpathy-skills:karpathy-guidelines` skill before writing any code, when
  it is installed. It is the house style for exactly this situation: executing a plan
  written earlier, where the failure modes are overcomplication, changes that drift past
  the request, and success claimed without a check. Skip it silently when the skill is not
  available — it is a quality lever, not a dependency.
- Work only from the plan. Do not redesign it, do not widen its scope, do not add
  speculative features.
- Follow the plan's own sections in order. **Commit once per section**, so the history
  matches the plan and a reviewer can read them side by side. Use the repository's commit
  convention.
- Each commit cites, in its subject, the short Nestor id of the task whose plan section it
  implements — unless that task is the one that owns the branch, which the PR title
  already cites. Use the short id, never the slug. A standalone task therefore carries no
  id in its commits, and a parent's subtasks each carry their own.
- Run that section's own verification **before** committing it. A section whose
  verification fails is not committed; report the failure instead of working around it.
- Never edit French prose with `sed`, `python` or any other string-rewriting shell tool.
  Accented characters and typographic apostrophes get mangled silently. Use the file
  editing tools.
- Report, per section: what changed, the verification command run, and its real output.

## Stage 4 — Audit what you wrote

This stage is not optional, and it is not a re-reading of your own Stage 3 report.

Having written the code is what makes this hard: you remember what you meant to do, and the
memory reads like evidence that it is there. It is not evidence. The diff and the real
output of each verification are.

Measure the work against the `andrej-karpathy-skills:karpathy-guidelines` checklist loaded
at Stage 3, when it is installed, rather than against a sense that the diff looks fine.

Then:

1. **Read every commit's diff.** Run `git log origin/<targetBranch>..HEAD`, then `git show`
   each commit. Look for scope creep, files touched for no reason, tests weakened to pass,
   comments that paraphrase the code.
2. **Re-run every verification command yourself**, from the plan, not from the report.
3. **Check the plan's own "done when" criteria** one by one against what you observe.

Fix what is wrong and commit each fix separately, one commit per concern. If the audit shows
the plan itself was wrong, stop and say so — do not quietly redesign it.

Report honestly: what passed, what you fixed, what still fails. A failing check reported
plainly is worth far more than a green summary that does not hold.

## Stage 5 — Close the task in Nestor

Set the task's status with `update_item` and pass them as `expectedVersion` and `expectedEtag`.

Use `completed` when every criterion passed. Use `need_review` when the work stands but
something still needs a human eye, and say what.

## Stage 6 — Open the pull request, then stop

Enter this stage once `targetBranch` is resolved: that happens when the arguments contain
`prod` or `target:<branch>`, or when the user answered Stage 2 with a target. Follow the
repository's own Git workflow.

1. Push the branch and open the PR with `gh`, explicitly passing `targetBranch` as its base.
   The title contains the short Nestor id of the task that owns the branch — the one
   Stage 2 settled on, which is the built task itself when it has no parent. Use the
   short id (for example `DsoA`), never the slug. The body describes what the task asked
   for and what the audit found; it may repeat this id, but the title is the required
   citation. Verify the PR's reported base branch and stop if it differs from
   `targetBranch`.
2. Report the PR URL and stop. Do not merge, do not wait for checks, do not tag.

Never force-push, never rewrite a published branch, and never bypass a commit hook with
`--no-verify`. If a hook refuses the commit, its diagnostic is the work to do.

## What this skill never does

- It never runs without a target. No argument means one line back to the user, nothing else.
- It never writes the plan. An incomplete task is refused at Stage 1, not repaired.
- It never substitutes a missing target branch without the user's confirmation.
- It never merges, waits for CI on `targetBranch`, or tags a release. The open PR is the end.
- It never trusts its own recollection of the work in place of the diff.
