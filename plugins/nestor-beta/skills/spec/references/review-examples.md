# Reviewing the compiled work

These are illustrative exchanges and a matrix of the expected paths. `A` is the agent and
`U` the user. Brackets describe the material displayed or the writes performed; they are
not placeholders to store in Nestor. Use the real items and the user's language. The
[MCP examples](mcp-examples.md) define the complete data written in every path.

## Detail typed: an existing Plan

The user invokes Spec on `gray_xerinae (dated CSV export)`. The interview establishes
that invalid dates must fail before records are selected, and archived records stay out.

> A: [saves the complete specifications and dependency of the existing Plan and its two Tasks, then approves the selected subtree once]
> A: `gray_xerinae (dated CSV export)` is saved, ready to build. Type detail to see the detail.
> U: detail
> A: [The saved Plan, any sub-plans and both code Tasks appear in the complete tree with their kinds. All six Plan fields, every Task's context, ordered actions and verification commands, completion criteria, the justified dependency, the existing items changed and every replaced field are displayed.]

The writes follow the interview in the same turn, with nothing displayed before.
`detail` only displays the saved work: no write follows it.

## Another answer: reorganising a standalone Task

The user invokes Spec on `copper_manatee (dated CSV export)`, an eligible standalone Task
that holds date validation and file generation. The interview resolves its scope.

> A: [saves every complete specification, creates the export Plan, attaches the same Task to it, adds the justified prerequisite, then approves the new Plan]
> A: `gray_xerinae (dated CSV export)` is saved, ready to build. Type detail to see the detail.
> U: Great, thanks.

Before any answer, the agent saves every complete specification, attaches the same Task
using `planId`, adds the justified prerequisite and approves the new Plan in the same
turn. It cites the actual returned slug for that new Plan. The Task remains a Task; an
eligible ordinary Task gains `template: "code"` without changing its identity. The detail
tree shows the reorganisation. An answer other than `detail` changes nothing that is
saved.

## Detail requested during the interview: an autonomous code Task

> U: Use Spec on `brown_turtle (reject invalid export dates)` and show me the full detail.
> A: [After resolving any business decisions and compiling the complete work, saves and approves the Task.]
> A: `brown_turtle (reject invalid export dates)` is saved, ready to build. [The autonomous code Task in its tree, the full context, steps with actions and executable verification commands, completion criteria, dependencies if any, and every replaced field.]

Nothing is displayed before the writes, even with this request. The detail follows the
status sentence, without the `detail` offer. Its repository, scheduling, identity and
unrelated content stay intact.

## Nine paths

For each row, check both the visible exchange and the complete saved work. In every path,
only interview questions precede the writes: no summary, display question or permission
request. The closing gives the citation and the actual status, then the `detail` offer
unless the detail was requested during the interview.

| Entry | Detail path | Before the writes | Saved work and approval | Closing | After the closing |
| --- | --- | --- | --- | --- | --- |
| Existing Plan | `detail` typed | Interview questions only | Same Plan and all remaining descendants, complete replacements; approve the selected subtree once | Citation, ready to build, `detail` offer | Every specification, typed tree, justified edges, changed items and replaced fields, without a write |
| Existing Plan | Other answer | Interview questions only | Same complete subtree and dependency data; approve once | Citation, ready to build, `detail` offer | Nothing changes |
| Existing Plan | Requested during the interview | Interview questions only | Same complete subtree; approve once | Citation, ready to build, then the full detail, without an offer | Nothing further |
| Task reorganised under a new Plan | `detail` typed | Interview questions, including the reorganisation when uncertain | New complete Plan, same existing Task attached through `planId`, other complete Tasks and edges; approve Plan once | Citation of the new Plan, ready to build, `detail` offer | New Plan and Tasks, retained Task identity, specifications, typed tree, justified edges and replaced fields, without a write |
| Task reorganised under a new Plan | Other answer | Interview questions, including the reorganisation when uncertain | Same complete Plan, Task specifications and edges; approve Plan once | Citation of the new Plan, ready to build, `detail` offer | Nothing changes |
| Task reorganised under a new Plan | Requested during the interview | Interview questions, including the reorganisation when uncertain | Same complete Plan and Tasks; approve Plan once | Citation of the new Plan, ready to build, then the full detail with the reorganisation, without an offer | Nothing further |
| Autonomous code Task | `detail` typed | Interview questions only | Same complete Task, with its own repository; approve Task | Citation, ready to build, `detail` offer | Task tree, full context, steps, checks, criteria, dependencies and replaced fields, without a write |
| Autonomous code Task | Other answer | Interview questions only | Same complete Task data; approve Task | Citation, ready to build, `detail` offer | Nothing changes |
| Autonomous code Task | Requested during the interview | Interview questions only | Same complete Task; approve Task | Citation, ready to build, then the full detail, without an offer | Nothing further |

## Exceptions at any detail level

> U: Keep it as a draft.
> A: [saves the complete specification without approving it]
> A: `brown_turtle (reject invalid export dates)` is saved as a draft, not approved. Type detail to see the detail.

Save the complete specification without approving it. “Save it, but approve later”
closes the same way with “saved, approval postponed”, whether or not the user asked for
the detail. Never use the `detail` offer or its answer to override an explicit limit.

> U: Stop here.
> A: The export work stops here. We can continue from the date-error decision later.

No write follows an explicit stop received before saving.

## Invariants

Every Plan and sub-plan keeps all six fields: `objective`, `requirements`, `architecture`,
`dataHandling`, `errorHandling` and `verificationPlan`. Every code Task keeps its complete
`context`, `steps[{action, verification}]` and `doneWhen`, plus justified dependencies.
No child is left to specify later. Completed work is preserved.

The `detail` offer and its answer change the display only and never condition a write.
Use the resolved scope and each item's current matched version/ETag pair for writes;
reconcile conflicts once under the skill's rules. Keep types, identities and scheduling.
Save all remaining work before atomic approval; respect draft, stop and later-approval
limits. Inspect readiness only on an explicit request. None of these examples starts a
build.
