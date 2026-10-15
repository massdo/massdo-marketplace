# Exchange examples

These exchanges illustrate the expected tone and closing of each flow. They support a
static review of this skill, not evidence of observed conversational behaviour. Conduct
the real exchange in the user's language, with the actual slugs and server results. `A`
is the agent and `U` the user; bracketed text summarises what the agent shows.

## Normal wording

Every question fits in one sentence and names the decision only. None of them repeats
this skill's path, quotes its rules, or asks for permission to compile, save or approve.
No exchange ends with a question about saving or approving the work.

Not this, before every question:

> The Spec skill (`…/skills/spec/SKILL.md`) requires: "Ask one real question at a time."
> This question settles the export format before compiling.

A higher-priority client instruction may still require naming or linking the skill when
it causes a question or a pause. Follow it in its shortest accepted form, next to the
question, without quoting rules around it. This skill cannot remove that obligation.

## Autonomous Task

The user invokes this skill with the idea "Reject invalid export dates".

> A: Should an invalid date return an error, or fall back to today?
> U: An error.
> A: [specification and tree] Saved and approved: `brown_turtle`, one code Task.

The last answer settles the last decision. In the same turn, the agent compiles the work,
shows it, creates the Task, approves it and reports the server's results.

## Complete Plan

The user invokes this skill with the idea "Export dated records to CSV".

> A: Should the export include archived records?
> U: No.
> A: [specifications, tree with each node's kind, dependencies] Saved and approved:
> `gray_xerinae`, one Plan and three code Tasks.

The agent writes the Plan, its code Tasks and their dependency edges, then approves the
Plan once: that approval covers its whole subtree.

## Rerun on approved work

The user invokes this skill on `copper_manatee`, an approved code Task of the approved
Plan `gray_xerinae`, to also export ISO week dates.

> A: Should a week date export the whole week or only its first day?
> U: The whole week.
> A: [changed fields] Saved and approved again: `copper_manatee`. The approval of
> `gray_xerinae` was revoked by this change; its other Tasks are outside this request.

The agent starts from the stored Task and keeps its identity, planning, Git references
and useful content. It resets no approval when the interview starts: the saved change
lets the domain revoke it, then the agent approves the requested Task again. The Plan's
subtree is not entirely within this request, so the agent reports its revoked approval
instead of approving it. Run on `gray_xerinae` itself, the same change ends with the
whole Plan approved again.

## Explicit stop or later approval

> U: Stop here, I'll come back to it later.

No write follows. When writes were already confirmed, the agent lists them.

> U: Save it, but don't approve it yet.
> A: [specification and tree] Saved, not approved: `brown_turtle`.

The agent does not ask for approval again later to get around that choice.

## Explicit draft

> U: Keep it as a draft.
> A: [specification and tree] Saved as a draft, not approved: `brown_turtle`.

## Reconcilable conflict

A save returns `CONFLICT` with `details.current`: someone renamed `gray_xerinae`
meanwhile. The new title contradicts no decision of the interview, so the agent keeps it,
reapplies its own changes to that state and retries once with the fresh pair, without a
question:

> A: Saved and approved: `gray_xerinae`, keeping the title changed meanwhile.

## Conflict that needs a decision

`details.current` shows that someone switched the export of `copper_manatee` from CSV to
JSON meanwhile, against an answer of the interview:

> A: `copper_manatee` was switched to JSON meanwhile. Should it keep CSV or JSON?
> U: CSV.
> A: Saved and approved: `copper_manatee`.

The agent asks only that question, then resumes saving and approving; it never asks for a
general confirmation instead. A second refusal stops the save; the agent reports the
confirmed ids and the exact unfinished node.

## Save or approval failure

> A: Saved `gray_xerinae` and two of its code Tasks. The third creation failed:
> <exact server error>. Nothing is approved.

Confirmed identities stay. A later attempt resumes from them without creating them again.

> A: Approval refused: `copper_manatee` has a step without verification. I added the
> repository's `pnpm test -- csv-export` to it: saved and approved.

When the missing content is a decision that belongs to the user, the agent asks only that
question. A refusal never turns into a validation question or hides the blocking item.
