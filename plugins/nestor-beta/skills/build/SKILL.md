---
name: build
description: Build one approved Nestor code Task or an approved Plan subtree into a shared open pull request, using the server's build reservation and progression decisions. Invoke only on the user's direct request with an explicit item id or slug; agents, plans, tasks and other skills cannot invoke it. Stop after verified delivery; never merge, wait for CI or deployment, publish a release, or tag.
argument-hint: "<plan-or-task-id-or-slug> [prod] [target:<branch>]"
disable-model-invocation: true
---

# Nestor Build

Execute the saved specification yourself, one code Task at a time. One explicit Plan
invocation authorises its server-selected subtree in this session; a Task invocation
selects only that Task. Never reinvoke a skill or create an agent or branch per child.
The server owns approval, selection, ordering, reservation and status transitions.

## Identify the plugin version

Pass `{ "version_hash": "23dd484c7787e7cd8" }` on every Nestor MCP call.

## Arguments

Accept `<id-or-slug> [prod] [target:<branch>]` only from a direct user invocation or an
explicit request for this process. A task mentioned in conversation is insufficient.
With an empty argument string, reply exactly and stop without searching:

> id or task slug is needed to build ! :)

The first argument identifies a Plan or code Task. The literal `prod` defaults the target
to `main`; a non-empty `target:<branch>` overrides it. Preserve everything after the first
colon, including `/`. An empty `target:` leaves the target unspecified. Reject unknown
arguments and multiple `target:` arguments, naming the invalid input. Without a resolved
target, ask for `target:<branch>` during preparation and wait.

## 1. Read and prepare before Git

Read the reference with `get_item(ref, scope: { mode: "global" }, known, version_hash)`.
Send the held matched `{ version, etag }` pair only with the necessary complete content;
otherwise send `known: null`. An unchanged response retains that content and pair and
refreshes the project name. A full response replaces them. Group known refs by up to five.

Read the server's published contracts. Require `manage_build` operations `inspect`,
`reserve`, `next`, `block`, `resume`, `complete`, `release` and `transfer`, plus the code-work
fields of `get_item` and `update_item`. If unavailable, stop before Git or writes; never
fall back to status patches. Read [the MCP call examples](references/mcp-examples.md) when
preparing calls; the current catalogue takes precedence.

Keep the selection id distinct from the shared context id and the active Task id. For a
Plan, read its mixed tree with `get_tree` and the complete member objects. Follow any
truncated or hidden subtree until the read is complete. For an attached Task, follow
`planId` and `parentPlanId` to the root Plan to read its inherited Git context. Historical
`parentTaskId` relations do not establish a Plan. Refuse ordinary Tasks and other item
types; do not convert, approve, or rewrite a specification to force a build.

For an explicit continuation of an existing owned reservation, reconcile its state through
section 5 first. Do not attempt a fresh reservation or restart already completed work.
An existing foreign reservation stops preparation; reads cannot recover its private proof.

Prepare a new build from these reads, then call `reserve` directly in section 2. It owns
eligibility, selection and dependency order; do not calculate a competing selection or use
`inspect` as a prerequisite. Keep `inspect` for an explicitly requested read-only diagnosis
or readiness check, including Spec; it is not an automatic response to a build refusal.

If the full read shows the requested Task completed, or a non-empty Plan subtree whose
code Tasks are all completed, report the completed selection and stop before reserve or
Git. Release a retained owned reservation explicitly through section 5 if present. If any
Task in the requested work is `need_review`, suspend the build; only explicit review
acceptance or correction work may continue through section 5. These observations do not
replace the server's eligibility decision for unfinished work.

Read the unfinished Tasks' full `specification`, declared dependency objects and completion
evidence, reusing held content and grouped conditional reads. Read required prerequisites
outside the requested subtree for their results, not to add them to the build. Refuse open
decisions, steps without executable verification and required actions the agent cannot
perform. Resolve the effective repository from the root Plan, or from the autonomous Task.
An incomplete plan is reported, never repaired here.

## 2. Validate Git, then reserve

Read `CLAUDE.md`, `AGENTS.md` and `CONTRIBUTING.md` where present. Their workflow and hooks
apply. Branch names, commit subjects and PR titles describe changes without Nestor ids or
slugs. Commit subjects, PR titles and PR descriptions are in English.

1. Check the checkout's `origin` URL, in HTTPS form without `.git`, against the effective
   repository. Confirm a clean working tree; never stash or discard user changes.
2. Run `git fetch --prune origin`, then
   `git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin`, excluding symbolic
   `HEAD`. Resolve the requested target exactly. Without one, show available branches and
   ask for `target:<branch>`. For a missing name, propose only a case-insensitive exact or
   unique one-edit match and wait for confirmation; otherwise request an available target.
   An empty remote list ends preparation. Never silently substitute a branch.
3. Read the root Plan's shared `git.targetBranch`, `git.workBranch` and `git.pullRequestUrl`
   (or the autonomous Task's Git fields). An attached direct build reuses that context;
   it does not create an independent PR. Read open PR footers with
   `gh pr list --state open --limit 1000 --json number,url,headRefName,baseRefName,body` and
   compare the actual contributing family with those references. Conflicting references,
   several matching PRs or a different base stop the build. Never infer ownership from
   a branch name. When exactly one PR matches, check its head and URL against any recorded
   references, then adopt its `headRefName` and `url` as the shared work branch and PR,
   including when those Git fields are missing in Nestor. Use these resolved references
   in step 4; persist missing fields only after reservation succeeds. If the target is
   unset, save the validated `git.targetBranch` with `update_item` on the context, using its
   held pair. Use the resulting pair when the context is also the selection; otherwise
   retain each object's own pair. Continue directly to reserve without an inspect call.
   A recorded different target requires explicit resolution.
4. Resolve the intended checkout to the shared work branch when present, otherwise
   `origin/<targetBranch>`. Before switching, inspect that ref read-only with Git. Check
   applicable cited files and symbols, allowing harmless line-number drift. For each external
   prerequisite, read its completion evidence and verify the required result in this ref,
   using its recorded commit where applicable. A completed status or open PR alone is
   insufficient. If a required result is absent, stop; never merge or cherry-pick it
   automatically. After reservation and checkout, confirm the files, symbols and relevant
   checks again in the actual working tree before editing. Anchors or results that an
   earlier internal Task must produce are checked when the dependent Task becomes active.
5. With no existing reservation, call `manage_build(operation: "reserve", id: selectionId)`
   with that item's latest held pair. It acquires the root context and starts the first
   eligible Task in `building`. A refusal ends preparation: report its code, message,
   `details.id` and `details.dependencyId` when supplied, without an automatic inspect.
   Never skip a refused child, reorder work or patch status to bypass the core. Only after
   success may you create or switch a work branch or edit code.

Retain ownership immediately on success. Use `reservation.contextId` for the shared Git
context, `selectionId` for this invocation and `taskIds` as the server's ordered selection.
Confirm the first id's current status with `get_item`; do not guess a child or call next
before completing it. Reuse the held specifications, dependencies and evidence for those
ids; read any missing content in groups of up to five. Reserve does not return the Tasks'
content or an `externalDependencies` list: use their declared dependencies and the complete
membership already read to find the required external results. Verify section 2.4 in the
resolved ref and actual checkout before editing. If the active Task is in review, suspend
for review or authorised corrections. If a persistent obstacle is discovered after reserve,
block the active building Task through section 5, retaining ownership and a resume condition;
never leave an acquired reservation without an explicit interruption, review or blockage
state. Changes to planned work require release and revised approval, not edits while reserved.

Retain returned `ownership: { executionId, proof }` privately for every reserved write.
Never print the proof or put it in files committed to Git, item bodies, PRs, logs, errors
or a transmission. Read APIs never return it. A reservation persists without expiry.
For an interrupted owned reservation, follow section 5 instead of calling reserve again.
A foreign reservation stops the build; only an explicit owner-authorised transfer can
replace its credential. Never fabricate an execution id or proof.

Reuse the shared work branch and PR resolved in step 2.3, whether recorded or found through
the footer. After reservation, save recovered `git.workBranch` and `git.pullRequestUrl`
together on the context through an owned `update_item` patch before editing. Create one
descriptive branch from `origin/<targetBranch>`, such as `feat/csv-export`, for the entire
root Plan only when neither recorded references nor a matching PR supply a work branch;
record `git.workBranch` on its context through an owned `update_item` patch. A reserved Git
patch may update workBranch and pullRequestUrl; repository, target, planned work, membership and
dependencies stay frozen. Revalidate the checkout and anchors before the first edit.

For every MCP mutation, use the matched pair belonging to the addressed item. Keep each
successful response's item version and ETag together. If a needed object's content or pair
is absent, read it once; never reuse a Task's pair for its context. On `CONFLICT` with
`details.current`, reconcile that state and retry once with its fresh pair, without an
extra read or blindly replaying the refused operation. Without that payload, conditionally
read once with `known` and retry once. A second refusal stops execution. Never bypass an
approval or ownership failure. A lost response has unknown outcome: reconcile confirmed
state before repeating any mutation, especially reserve or transfer.

## 3. Implement and audit the active Task

Reread the active Task's full held specification before editing. Load installed
`karpathy-guidelines` when available. Follow its sections in order and change only what
the specification requires. Never edit French prose with string-rewriting shell tools;
use file editing tools. For each Task started by next, repeat section 2.4's ref and checkout
checks for its anchors and prerequisite results before editing.

Implement one Task at a time on the common branch. Run each section's verification before
committing that section, using the repository's convention. Keep one descriptive commit
per section and report the command and real output. Diagnose and fix ordinary correctable
failures without inventing a successful result. Run the Task's atomic checks and all
required repository checks before recording completion.

Audit the actual diffs yourself: run `git log origin/<targetBranch>..HEAD`, then `git show`
for every commit. Check scope, unrelated files and weakened tests against the installed
Karpathy checklist. Rerun every declared verification from the specification and check
each `doneWhen` criterion against observations. Commit audit fixes separately, one concern
per commit. If the specification itself is wrong, stop and report it without redesigning.

## 4. Deliver, complete, then advance

For the active Task, before completion:

1. Push the common branch without force or history rewriting. Open or update its common PR
   with `gh`, explicitly using `targetBranch` as base when creating it. Keep hooks enabled.
   Adjust the English title and description to the complete current scope.
2. End its description with one visible last line, nothing after it:

   ```
   nestor tasks: brown_turtle, gray_xerinae, copper_manatee
   ```

   Use exact returned slugs, once each, comma-space separated. Keep existing contributors
   and add the Tasks and Plans the changes actually contribute to; dependencies alone do
   not belong. Keep all Nestor references in this footer.
3. Read back `gh pr view --json url,state,title,body,baseRefName,headRefName,headRefOid`.
   Verify OPEN, target base, common head branch, English descriptive title and footer.
   Check the full local commit SHA against the pushed remote head and PR head. Correct
   metadata and reread when needed. A failed push, missing PR or wrong reference stops
   completion. Record the verified `git.pullRequestUrl` on the context with ownership.
4. Call `manage_build(operation: "complete", id: activeTaskId)` with that Task's held pair,
   ownership and `completionEvidence`: an observed result for every exact `doneWhen`
   criterion and every exact step verification command, the full pushed commit SHA, and
   the verified open PR. Use `review: "none"` only when every criterion passes. When work
   stands but human review is required, record `review: "requested"`; the returned
   `need_review` suspends the whole cascade. Never claim unexecuted checks passed or
   manufacture evidence. A failing required check cannot complete the Task.

Only after confirmed completion may a Plan build call `manage_build(operation: "next",
id: selectionId)` with ownership and that item's current pair. It rechecks the selection
and starts the next authorised Task. Its returned `item.id` identifies that Task; read its
full content and repeat sections 3–4, without invoking a skill again. A direct Task build
ends with its single Task, even when siblings remain.

Any refusal, blockage or `need_review` stops the loop. Never try other children. The root
Plan's completion is derived from all actionable Tasks, including those outside a directly
built Task or selected sub-plan; never patch the root completed yourself.

When the selected work is confirmed complete, call `manage_build(operation: "release")`
explicitly on the context with its current pair and ownership. The last completion alone
does not release it. Report the PR URL, verified results and confirmed Task/Plan progress,
then stop. Never merge, wait for CI or deployment, publish a release, or create a tag.
Local results and an open PR are delivery evidence, not production proof.

## 5. Block, interrupt and resume

For a persistent obstacle on an active building Task, call `manage_build(operation:
"block", id: activeTaskId)` with ownership, its held pair, and non-empty
`blockage: { reason, resumeCondition }`. Report the exact obstacle and stop. It retains
the reservation and suspends every remaining Task. Ordinary correctable errors need no
persistent blockage. An interruption also retains the reservation; do not silently release.

On an explicit continuation, read the selection, root context, remaining Tasks and shared
Git references with conditional reads. Keep completed Tasks and their evidence; never
rebuild them or recreate children. If the selected work is already completed, release its
retained reservation with the current context pair and ownership, then stop before Git.
Otherwise reconcile the held reservation's `contextId`, `selectionId` and ordered `taskIds`
with those reads. Validate the repository, current checkout, pushed head and open PR against
the shared Git references again, including section 2.4's prerequisite checks. Do not call
reserve again or insert an automatic inspect into a continuation. Review still requires
explicit acceptance or correction authorisation; otherwise keep the build suspended.
Use the retained private ownership. If another execution must take over, require explicit
transfer by the current owner via `manage_build(operation: "transfer")`; it returns a new
credential and revokes the old one immediately. Missing proof is not authority to recover
it through reads, reserve again, or remove the reservation.

After observing that a stored resumeCondition is resolved, call `manage_build(operation:
"resume", id: activeTaskId, conditionResolved: true)` with ownership and its current pair.
For review corrections without blockage, resume may use false. Continue the interrupted
Task only after acceptance. An already building unblocked Task can continue with its owned
reservation without an invalid resume call; if no Task is active and work remains in a
selected Plan, use next with the selection's current pair. Use `complete(review: "accepted")`
only after actual acceptance of the reviewed work, with valid evidence; never grant that
acceptance yourself to skip review.

If planned work must change, release explicitly before seeking revised specification and
approval; do not edit frozen work. An explicit abandonment may also release the context:
the server retains completed work and restores eligible unfinished Tasks to ready_to_build.
