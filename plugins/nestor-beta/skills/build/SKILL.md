---
name: build
description: Build a specified Nestor task end to end into a validated target branch, delegate its implementation, audit every commit, close the task, and optionally ship with prod after explicit confirmation. Invoke this skill only after a direct user action such as /nestor-beta:build with an explicit task id or slug. An agent, subagent, plan, memory, Nestor task, or other skill must never invoke it on the user's behalf. A task mentioned in conversation is not a build request.
disable-model-invocation: true
---

# Nestor Build

Turn a Nestor task into merged code. The task is the specification: this skill never
invents the plan, it executes the one already written and then checks that the execution
matches it.

Two models share the work. A cheaper subagent writes the code, because following an
explicit plan is the part that does not need the strongest model. You — the parent, expert
model — set the stage, audit the result, and own every irreversible action: merge, tag,
push.

## Identify the plugin version

Pass `{ "version_hash": "e1f345d3a9652117" }` on every Nestor MCP call.

## Arguments

```
/nestor-beta:build <id-or-slug> [prod] [target:<branch>]
```

**An empty argument string ends the turn immediately.** Reply exactly:

> id or task slug is needed to build ! :)

Then stop. Do not list tasks, do not search Nestor for a plausible candidate, and do not
reuse a task mentioned earlier in the conversation. The user always knows the id they mean,
and a wrong guess here is only discovered after a branch and a subagent run — the most
expensive way to learn that the target was wrong.

The first argument is a Nestor item id or a `color_animal` slug. Pass it to `get_item` as
`id` or as `slug`, never both — the shape tells you which: a slug carries an underscore.

After the first argument, parse these optional named arguments in any order:

- The literal flag `prod` requests the shipping stage. It does not authorize that stage by
  itself; Stage 6 still requires a separate explicit confirmation from the user.
- One `target:<branch>` argument selects the remote branch into which the PR will merge.
  Preserve everything after the first colon, including `/` in branch names. An absent
  argument or an empty `target:` leaves the target unspecified until Stage 2.

Reject more than one `target:` argument or any unknown argument. Name the invalid argument
and stop rather than guessing.

Without `prod`, the skill stops on a branch with commits and a closed task. That is the
common case and the safe default: shipping stays an explicit request.

## Stage 1 — Load the task and decide whether it can be built at all

Read the task with `get_item`. Then read its body as an executor would, and answer one
question: could someone implement this without asking anything?

Refuse and stop when you find any of these:

- **An open decision.** A sentence like "decide whether X or Y" means the plan is not
  finished. Executing it would make the subagent choose on the user's behalf.
- **A step with no verification.** A step that cannot be checked cannot be reported as
  done, and a subagent will report it as done anyway.
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

## Stage 3 — Delegate the implementation

Spawn one subagent with the `Agent` tool, `model: "sonnet"`, and let it run to completion.
Sonnet is the deliberate choice here: a multi-file refactor with intermediate commits has
to hold a plan across many turns, and a model that drifts costs more in audit than it saves
in tokens.

Give it the task body **verbatim**. Do not summarize it — the summary is where the
constraints get lost.

The prompt must carry these instructions:

- Load the `andrej-karpathy-skills:karpathy-guidelines` skill before writing any code, when
  it is installed. It is the house style for exactly this situation: an executor working
  from someone else's plan, where the failure modes are overcomplication, changes that
  drift past the request, and success claimed without a check. Skip it silently when the
  skill is not available — it is a quality lever, not a dependency.
- Work only from the plan. Do not redesign it, do not widen its scope, do not add
  speculative features.
- Follow the plan's own sections in order. **Commit once per section**, so the history
  matches the plan and a reviewer can read them side by side. Use the repository's commit
  convention.
- Run that section's own verification **before** committing it. A section whose
  verification fails is not committed; report the failure instead of working around it.
- Never edit French prose with `sed`, `python` or any other string-rewriting shell tool.
  Accented characters and typographic apostrophes get mangled silently. Use the file
  editing tools.
- Report, per section: what changed, the verification command run, and its real output.

## Stage 4 — Audit the work yourself

This stage is not optional, and it is not a re-reading of the subagent's report.

An executor subagent reliably reports success on criteria it did not actually verify. Its
report is a claim, not evidence.

Load `andrej-karpathy-skills:karpathy-guidelines` here too, when it is installed. The
subagent was asked to follow it; reading the same guidelines gives you the checklist its
work should be measured against, rather than a vague sense that the diff looks fine.

Then:

1. **Read every commit's diff.** Run `git log origin/<targetBranch>..HEAD`, then `git show`
   each commit. Look for scope creep, files touched for no reason, tests weakened to pass,
   comments that paraphrase the code.
2. **Re-run every verification command yourself**, from the plan, not from the report.
3. **Check the plan's own "done when" criteria** one by one against what you observe.

Fix what is wrong and commit the fixes yourself, one commit per concern. If the audit shows
the plan itself was wrong, stop and say so — do not quietly redesign it.

Report honestly: what passed, what you fixed, what still fails. A failing check reported
plainly is worth far more than a green summary that does not hold.

## Stage 5 — Close the task in Nestor

Set the task's status with `update_item` and pass them as `expectedVersion` and `expectedEtag`.

Use `completed` when every criterion passed. Use `need_review` when the work stands but
something still needs a human eye, and say what.

## Stage 6 — Ship — only with `prod` and explicit confirmation

Everything in this stage is irreversible or public. Enter it only when the arguments
contain the exact `prod` flag, and follow the repository's own Git workflow.

Before any push, PR creation, merge, or tag, ask the user to confirm the shipping stage.
Name the work branch, `targetBranch`, and the planned push, PR, merge, CI wait, and release
tag. Then stop and wait. The `prod` flag in the original invocation is a request for this
confirmation, not the confirmation itself. Continue only after an unambiguous affirmative
reply; a refusal or ambiguous reply leaves the audited branch and commits in place without
shipping.

1. Push the branch and open the PR with `gh`, explicitly passing `targetBranch` as its base.
   The body describes what the task asked for and what the audit found. Verify the PR's
   reported base branch and stop if it differs from `targetBranch`.
2. **Wait for the PR checks before merging** — `gh pr checks <number> --watch`. Merging into
   a protected branch on a red check is the one mistake this whole flow cannot undo. If the
   user prefers merging first, this is the line to remove.
3. Merge. Prefer a merge that preserves the per-section commits, since that history is the
   point of Stage 3.
4. Wait for CI to go green **on `targetBranch` after the merge**, not only on the PR. Two
   branches passing separately does not prove their merge passes.
5. Derive the release version from the merged commits: a breaking change (`!` or
   `BREAKING CHANGE`) bumps major, any `feat` bumps minor, otherwise patch. Read the latest
   existing tag for the current number.
6. **Announce the computed version and tag it** — `vX.Y.Z` — then push the tag.

Never force-push, never rewrite a published branch, and never bypass a commit hook with
`--no-verify`. If a hook refuses the commit, its diagnostic is the work to do.

## What this skill never does

- It never runs without a target. No argument means one line back to the user, nothing else.
- It never writes the plan. An incomplete task is refused at Stage 1, not repaired.
- It never substitutes a missing target branch without the user's confirmation.
- It never ships without both `prod` and a separate explicit confirmation.
- It never trusts a subagent's report in place of the diff.
