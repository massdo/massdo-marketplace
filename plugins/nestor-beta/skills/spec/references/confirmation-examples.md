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
> A: [specification and tree] `brown_turtle (reject invalid export dates)` will reject invalid dates with an error. To implement it, run `/nestor-beta:build brown_turtle target:main`.

The last answer settles the last decision. In the same turn, the agent compiles the work,
shows it, creates the Task, approves it and closes with the user outcome and next choice.

## Complete Plan

The user invokes this skill with the idea "Export dated records to CSV".

> A: Should the export include archived records?
> U: No.
> A: [specifications, tree with each node's kind, dependencies] `gray_xerinae (dated CSV export)` will export dated records without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`.

The agent writes the Plan, its code Tasks and their dependency edges, then approves the
Plan once: that approval covers its whole subtree.

## Rerun on approved work

The user invokes this skill on `copper_manatee`, an approved code Task of the approved
Plan `gray_xerinae`, to also export ISO week dates.

> A: Should a week date export the whole week or only its first day?
> U: The whole week.
> A: [changed fields] `copper_manatee (week-date export)` will export the whole ISO week. You can build this change with `/nestor-beta:build copper_manatee target:main`; to build the whole export instead, first revisit `gray_xerinae (dated CSV export)` with Spec.

The agent starts from the stored Task and keeps its identity, planning, Git references
and useful content. It resets no approval when the interview starts: the saved change
lets the domain revoke it, then the agent approves the requested Task again. The Plan's
subtree is not entirely within this request, so the agent explains the next action needed
for a whole-Plan build instead of approving it. Run on `gray_xerinae` itself, the same change ends with the
whole Plan approved again.

## Explicit stop or later approval

> U: Stop here, I'll come back to it later.

No write follows. The closing describes only the work available for a later continuation:

> A: The export work stops here. When you return, we can finish how invalid dates are handled.

> U: Save it, but don't approve it yet.
> A: [specification and tree] `brown_turtle (reject invalid export dates)` describes the date-error behaviour for later review. It is not ready to build yet; return to Spec when you want to proceed.

The agent does not ask for approval again later to get around that choice.

## Explicit draft

> U: Keep it as a draft.
> A: [specification and tree] `brown_turtle (reject invalid export dates)` outlines the date-error behaviour. Return to Spec to finish it before building.

## Reconcilable conflict

A save returns `CONFLICT` with `details.current`: someone renamed `gray_xerinae`
meanwhile. The new title contradicts no decision of the interview, so the agent keeps it,
reapplies its own changes to that state and retries once with the fresh pair, without a
question:

> A: `gray_xerinae (dated CSV export)` will export dated records without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`.

## Conflict that needs a decision

`details.current` shows that someone switched the export of `copper_manatee` from CSV to
JSON meanwhile, against an answer of the interview:

> A: `copper_manatee (week-date export)` now calls for JSON. Should the export use CSV or JSON?
> U: CSV.
> A: `copper_manatee (week-date export)` will use CSV. To implement it, run `/nestor-beta:build copper_manatee target:main`.

The agent asks only that question, then resumes saving and approving; it never asks for a
general confirmation instead. A second refusal stops the save; the agent explains which
part of the export still needs attention and the action needed to continue.

## Save or approval failure

> A: `gray_xerinae (dated CSV export)` is not ready to build because the date-validation work could not be added. Retry Spec on this Plan to finish that part.

Confirmed identities stay. A later attempt resumes from them without creating them again.

> A: `copper_manatee (week-date export)` now includes a way to check the CSV result. To implement it, run `/nestor-beta:build copper_manatee target:main`.

When the missing content is a decision that belongs to the user, the agent asks only that
question. A refusal never turns into a validation question or hides the blocking item.

## Internal narration to avoid

Do not write:

> The export Task is completed, and its reservation is released.

Write the user outcome and useful next choice instead:

> The CSV export is available in [the pull request](https://github.com/example/repository/pull/42). Review and merge it when you are ready.

When a prerequisite PR is still pending, explain the dependency in the same terms:

> `gray_xerinae (dated CSV export)` will add CSV export. Merge [the date-parser PR](https://github.com/example/repository/pull/41) first, then run `/nestor-beta:build gray_xerinae target:main`.
