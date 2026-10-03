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

Pass `{ "version_hash": "26d77f90eff9c58d4" }` on every Nestor MCP call.

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
to `get_item` in `ref`, with `scope: { mode: "global" }`, `known` and `version_hash`. Send
the matched `{ version, etag }` pair only when the necessary task content is held; otherwise
send `known: null`. With `unchanged: true`, keep that content and pair and refresh the
project name; a full response replaces them. Never omit `known` or use null to re-read
held content with its pair. The server resolves the reference; do not select an input
field from an underscore or another character.

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
its branch naming, commit convention and Git workflow. They win over anything here, with
one exception: a Nestor id or slug never goes in a branch name, a commit subject or a pull
request title, and that title is in English. This skill orchestrates; the repository
decides its own conventions.

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
5. Decide which work branch to use. **A parent task and its subtasks are one deliverable:
   they ship together, in one pull request on one branch.** Read the task's family in
   Nestor, whatever the status of its members: its parent and that parent's subtasks when
   it has a `parentTaskId`, otherwise the task itself and its own subtasks. Then read the
   footer of every open pull request — the `nestor tasks:` line that ends its description,
   see Stage 5 — with
   `gh pr list --state open --limit 1000 --json number,headRefName,baseRefName,body`. A
   pull request whose footer lists a slug of that family is the family's: continue on its
   head branch. Its base must be `targetBranch`; if it differs, or if several pull requests
   match, say so and stop. The footer and Nestor's parent/child relations are the only
   link: never infer it from a branch name.
6. Otherwise create a fresh branch from `origin/<targetBranch>` with a descriptive name: the
   commit type that fits the work, then a few words about the change — `feat/csv-export`,
   `fix/login-redirect`.

## Stage 3 — Implement the plan

Write the code yourself, in this session, working from the task body as it stands. Reread it
**in full** from the held content before the first edit and keep it open: the mental summary
you would otherwise work from is where the constraints get lost.

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
- Keep every commit subject descriptive: it says what the commit changes and carries no
  Nestor id or slug. The task is referenced in one place only, the pull request footer of
  Stage 5.
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

## Stage 5 — Open the pull request and verify it

Enter this stage once `targetBranch` is resolved: that happens when the arguments contain
`prod` or `target:<branch>`, or when the user answered Stage 2 with a target. Follow the
repository's own Git workflow.

1. Push the branch. When Stage 2 found the family's pull request, keep working in it;
   otherwise open one with `gh`, explicitly passing `targetBranch` as its base.
2. Give it an English title that describes the change, without any Nestor id or slug.
3. Describe the changes and their validation in the body, as for any pull request, and
   keep Nestor references out of that text. They go in the footer: one visible line, the
   last of the description, with nothing after it — a signature or attribution line goes
   above.

   ```
   nestor tasks: brown_turtle, gray_xerinae, copper_manatee
   ```

   - Write each task's slug exactly as Nestor returns it, never an id: an id comes back
     shortened to a length that varies from one response to the next, a slug does not.
   - Separate them with a comma and a space, and write each slug once.
   - List the tasks the changes actually contribute to, the subtasks concerned included. A
     task that is only mentioned as a dependency stays out.
   - A partial contribution may be listed: the footer links a task to the code, it does
     not declare the task finished.

   Keep the footer true as the pull request evolves: when a subtask joins a pull request,
   keep every slug already listed and add the new ones, and adjust the title when the scope
   changes.
4. Read the pull request back with `gh pr view --json url,title,body,baseRefName` and
   check what GitHub reports: the title, the footer, and the base branch, which must be
   `targetBranch`. Correct a title or a footer that does not conform, then read again. If
   the pull request could not be created, or if a check still fails — a base that differs
   from `targetBranch` included — say what failed and stop: the task keeps its current
   status.

Never force-push, never rewrite a published branch, and never bypass a commit hook with
`--no-verify`. If a hook refuses the commit, its diagnostic is the work to do.

## Stage 6 — Close the task in Nestor, then stop

The task takes its final status only once its pull request is open and verified. Set it
with `update_item`, passing the held `{ version, etag }` pair as `expectedVersion` and
`expectedEtag`.

Use `completed` when every criterion passed. Use `need_review` when the work stands but
something still needs a human eye, and say what.

Report the PR URL and stop. Do not merge, do not wait for checks, do not tag.

## What this skill never does

- It never runs without a target. No argument means one line back to the user, nothing else.
- It never writes the plan. An incomplete task is refused at Stage 1, not repaired.
- It never substitutes a missing target branch without the user's confirmation.
- It never merges, waits for CI on `targetBranch`, or tags a release. The open PR is the end.
- It never trusts its own recollection of the work in place of the diff.
- It never writes a Nestor id or slug in a branch name, a commit subject or a pull request
  title. The footer is the only reference.
- It never gives the task its final status before its pull request is open and verified.
