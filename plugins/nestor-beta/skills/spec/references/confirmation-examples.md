# Exchange examples

These exchanges illustrate the expected tone and closing of each flow. They support a
static review of this skill, not evidence of observed conversational behaviour. Conduct
the real exchange in the user's language, with the actual slugs and server results. `A`
is the agent and `U` the user; bracketed text summarises what the agent shows or does.
For the complete presentation matrix, see [the review examples](review-examples.md).

## Normal wording

Every question fits in one sentence and names the decision only. None of them repeats
this skill's path, quotes its rules, or asks for permission to compile, save or approve.
No exchange asks a display question before the writes or ends with a question about
saving or approving the work.

Not this, before every question:

> The Spec skill (`…/skills/spec/SKILL.md`) requires: "Ask one real question at a time."
> This question settles the export format before compiling.

Not this either, after the summary, as happened on 18 October 2026:

> The Spec skill (`…/skills/spec/SKILL.md`) makes me wait for your answer before any write: I am only waiting for your display choice before saving the Task.

That pause existed for a display choice alone, and the user read it as a new request for
validation. Save and approve in the same turn as the summary, then offer the detail.

A higher-priority client instruction may still require naming or linking the skill when
it causes a real question or pause. Follow it in its shortest accepted form, next to the
question, without quoting rules around it. This skill cannot remove that obligation.

## Autonomous Task

The user invokes this skill with the idea "Reject invalid export dates".

> A: Should an invalid date return an error, or fall back to today?
> U: An error.
> A: Invalid export dates will return a clear error before any records are read. I will create one validation Task; existing records stay unchanged.
> A: [creates and approves the fully specified Task]
> A: `brown_turtle (reject invalid export dates)` is saved and approved, ready to build: it will reject invalid dates with an error. To implement it, run `/nestor-beta:build brown_turtle target:main`. Would you like to see the complete detail?
> U: No.

The business answer settles the last requirement; the agent compiles the complete work
before the summary. The summary, the writes and the closing happen in the same turn,
without waiting for an answer. "No" changes nothing: the Task is already saved and
approved.

## Complete Plan

The user invokes this skill with the idea "Export dated records to CSV".

> A: Should the export include archived records?
> U: No.
> A: You will get a CSV for the selected date, without archived records. I will create an export Plan covering date validation and file generation; validation comes first and existing records stay unchanged.
> A: [creates the Plan, its code Tasks and their dependency edges, then approves the Plan once]
> A: `gray_xerinae (dated CSV export)` is saved and approved, ready to build: it will export dated records without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`. Would you like to see the complete detail?
> U: Yes.
> A: [saved specifications, tree with each node's kind, justified dependencies]

The Plan's approval covers its whole subtree. "Yes" displays the saved work and writes
nothing.

## Rerun on approved work

The user invokes this skill on `copper_manatee`, an approved code Task of the approved
Plan `gray_xerinae`, to also export ISO week dates, explicitly requesting full detail.

> A: Should a week date export the whole week or only its first day?
> U: The whole week.
> A: [changed fields, shown before the writes]
> A: `copper_manatee (week-date export)` is saved and approved again, ready to build: it will export the whole ISO week. You can build this change with `/nestor-beta:build copper_manatee target:main`; to build the whole export instead, first revisit `gray_xerinae (dated CSV export)` with Spec.

The agent starts from the stored Task and keeps its identity, planning, Git references
and useful content. It resets no approval when the interview starts: the saved change
lets the domain revoke it, then the agent approves the requested Task again. The Plan's
subtree is not entirely within this request, so the agent explains the next action needed
for a whole-Plan build instead of approving it. Run on `gray_xerinae` itself, the same change ends with the
whole Plan approved again. The detail was shown before the writes, so the closing does
not offer it again.

## Explicit stop or later approval

> U: Stop here, I'll come back to it later.

No write follows. The closing describes only the work available for a later continuation:

> A: The export work stops here. When you return, we can finish how invalid dates are handled.

> U: Save it, but don't approve it yet, and show the full detail.
> A: [specification and tree, shown before the writes]
> A: `brown_turtle (reject invalid export dates)` is saved, approval postponed: it describes the date-error behaviour for later review. It is not ready to build yet; return to Spec when you want to proceed.

The agent does not ask for approval again later to get around that choice.

## Explicit draft

> U: Keep it as a draft and show the full detail.
> A: [specification and tree, shown before the writes]
> A: `brown_turtle (reject invalid export dates)` is saved as a draft, not approved: it outlines the date-error behaviour. Return to Spec to finish it before building.

## Reconcilable conflict

A save returns `CONFLICT` with `details.current`: someone renamed `gray_xerinae`
meanwhile. The new title contradicts no decision of the interview, so the agent keeps it,
reapplies its own changes to that state and retries once with the fresh pair, without a
question:

> A: `gray_xerinae (dated CSV export)` is saved and approved, ready to build: it will export dated records without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`. Would you like to see the complete detail?

## Conflict that needs a decision

`details.current` shows that someone switched the export of `copper_manatee` from CSV to
JSON meanwhile, against an answer of the interview:

> A: `copper_manatee (week-date export)` now calls for JSON. Should the export use CSV or JSON?
> U: CSV.
> A: `copper_manatee (week-date export)` is saved and approved, ready to build: it will use CSV. To implement it, run `/nestor-beta:build copper_manatee target:main`. Would you like to see the complete detail?

The agent asks only that question, then resumes saving and approving; it never asks for a
general confirmation instead. A second refusal stops the save; the agent says which part
of the export was not saved or approved and the action needed to continue.

## Save or approval failure

> A: `gray_xerinae (dated CSV export)` is saved without its date-validation work, which could not be added, and it is not approved, so it is not ready to build. Retry Spec on this Plan to finish that part.

Confirmed identities stay. A later attempt resumes from them without creating them again
and without a replacement validation question.

> A: `copper_manatee (week-date export)` is saved and approved, ready to build: it now includes a way to check the CSV result. To implement it, run `/nestor-beta:build copper_manatee target:main`. Would you like to see the complete detail?

When the missing content is a decision that belongs to the user, the agent asks only that
question. A refusal never turns into a validation question or hides the blocking item.

## Internal narration to avoid

Do not write:

> The export Task is completed, and its reservation is released.

Write the user outcome and useful next choice instead:

> The CSV export is available in [the pull request](https://github.com/example/repository/pull/42). Review and merge it when you are ready.

When a prerequisite PR is still pending, explain the dependency in the same terms:

> `gray_xerinae (dated CSV export)` will add CSV export. Merge [the date-parser PR](https://github.com/example/repository/pull/41) first, then run `/nestor-beta:build gray_xerinae target:main`.

The result of Spec's writes is the one exception: say it in plain words, never with
versions, ETags or technical identifiers.

> Not this: The Task was created at version 3, then approved.
> This: `brown_turtle (reject invalid export dates)` is saved and approved, ready to build.
