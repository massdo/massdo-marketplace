# Exchange examples

These exchanges illustrate the expected tone and closing of each flow. They support a
static review of this skill, not evidence of observed conversational behaviour. Conduct
the real exchange in the user's language, with the actual slugs and server results. `A`
is the agent and `U` the user; bracketed text summarises what the agent shows or does.
For the complete closing matrix, see [the review examples](review-examples.md).

## Normal wording

Every question fits in one sentence and names the decision only. None of them repeats
this skill's path, quotes its rules, or asks for permission to compile, save or approve.
Only interview questions precede the writes: no summary, no display question, and no
exchange ends with a question about saving or approving the work.

Not this, before every question:

> The Spec skill (`…/skills/spec/SKILL.md`) requires: "Ask one real question at a time."
> This question settles the export format before compiling.

Not this either, after compiling the work, as happened on 18 October 2026:

> The Spec skill (`…/skills/spec/SKILL.md`) makes me wait for your answer before any write: I am only waiting for your display choice before saving the Task.

That pause existed for a display choice alone, and the user read it as a new request for
validation. Save and approve in the same turn, then report the status.

A higher-priority client instruction may still require naming or linking the skill when
it causes a real question or pause. Follow it in its shortest accepted form, next to the
question, without quoting rules around it. This skill cannot remove that obligation.

## Autonomous Task

The user invokes this skill with the idea "Reject invalid export dates".

> A: Should an invalid date return an error, or fall back to today?
> U: An error.
> A: [creates and approves the fully specified Task]
> A: `brown_turtle (reject invalid export dates)` is saved, ready to build. Type detail to see the detail.
> U: Thanks.

The business answer settles the last requirement; the agent compiles the complete work,
then saves and approves it in the same turn, with nothing displayed before. An answer
other than `detail` changes nothing that is saved.

## Complete Plan

The user invokes this skill with the idea "Export dated records to CSV".

> A: Should the export include archived records?
> U: No.
> A: [creates the Plan, its code Tasks and their dependency edges, then approves the Plan once]
> A: `gray_xerinae (dated CSV export)` is saved, ready to build. Type detail to see the detail.
> U: detail
> A: [saved specifications, tree with each node's kind, justified dependencies]

The Plan's approval covers its whole subtree. `detail` displays the saved work and writes
nothing.

## Rerun on approved work

The user invokes this skill on `copper_manatee`, an approved code Task of the approved
Plan `gray_xerinae`, to also export ISO week dates, explicitly requesting full detail.

> A: Should a week date export the whole week or only its first day?
> U: The whole week.
> A: [saves the changed Task and approves it again]
> A: `copper_manatee (week-date export)` is saved, ready to build; `gray_xerinae (dated CSV export)` is no longer approved, so revisit it with Spec before building the whole export. [changed fields and the Task's full detail]

The agent starts from the stored Task and keeps its identity, planning, Git references
and useful content. It resets no approval when the interview starts: the saved change
lets the domain revoke it, then the agent approves the requested Task again. The Plan's
subtree is not entirely within this request, so the agent states the Plan's status and
the action needed instead of approving it. Run on `gray_xerinae` itself, the same change
ends with the whole Plan approved again. The detail requested during the interview follows
the status sentence, without the `detail` offer.

## Explicit stop or later approval

> U: Stop here, I'll come back to it later.

No write follows. The closing describes only the work available for a later continuation:

> A: The export work stops here. When you return, we can finish how invalid dates are handled.

> U: Save it, but don't approve it yet.
> A: [saves the complete Task without approving it]
> A: `brown_turtle (reject invalid export dates)` is saved, approval postponed. Type detail to see the detail.

The agent does not ask for approval again later to get around that choice.

## Explicit draft

> U: Keep it as a draft and show the full detail.
> A: [saves the complete Task without approving it]
> A: `brown_turtle (reject invalid export dates)` is saved as a draft, not approved. [specification and tree]

## Reconcilable conflict

A save returns `CONFLICT` with `details.current`: someone renamed `gray_xerinae`
meanwhile. The new title contradicts no decision of the interview, so the agent keeps it,
reapplies its own changes to that state and retries once with the fresh pair, without a
question:

> A: `gray_xerinae (dated CSV export)` is saved, ready to build. Type detail to see the detail.

## Conflict that needs a decision

`details.current` shows that someone switched the export of `copper_manatee` from CSV to
JSON meanwhile, against an answer of the interview:

> A: `copper_manatee (week-date export)` now calls for JSON. Should the export use CSV or JSON?
> U: CSV.
> A: `copper_manatee (week-date export)` is saved, ready to build. Type detail to see the detail.

The agent asks only that question, then resumes saving and approving; it never asks for a
general confirmation instead. A second refusal stops the save; the agent says which part
of the export was not saved or approved and the action needed to continue.

## Save or approval failure

> A: `gray_xerinae (dated CSV export)` is saved without its date-validation work, which could not be added, and it is not approved. Retry Spec on this Plan to finish that part.

Confirmed identities stay. A later attempt resumes from them without creating them again
and without a replacement validation question.

An approval refused because a CSV check is missing is completed from the repository, then
approved again:

> A: `copper_manatee (week-date export)` is saved, ready to build. Type detail to see the detail.

When the missing content is a decision that belongs to the user, the agent asks only that
question. A refusal never turns into a validation question or hides the blocking item.

## Internal narration to avoid

Do not write:

> The export Task is completed, and its reservation is released.

Write the user outcome and useful next choice instead:

> The CSV export is available in [the pull request](https://github.com/example/repository/pull/42). Review and merge it when you are ready.

The status of Spec's writes is the one exception: say it in plain words, never with
versions, ETags or technical identifiers beyond the citation.

> Not this: The Task was created at version 3, then approved.
> This: `brown_turtle (reject invalid export dates)` is saved, ready to build. Type detail to see the detail.

When a prerequisite PR is still pending, say so with the status:

> `gray_xerinae (dated CSV export)` is saved, ready to build once [the date-parser PR](https://github.com/example/repository/pull/41) is merged. Type detail to see the detail.
