# Reviewing the compiled work

These are illustrative exchanges and a static review matrix, not observed runtime
behaviour. `A` is the agent and `U` the user. Brackets describe the material displayed
or the writes performed; they are not placeholders to store in Nestor. Use the real items
and the user's language. The [MCP examples](mcp-examples.md) define the complete data
written in every path.

## Yes: an existing Plan

The user invokes Spec on `gray_xerinae (dated CSV export)`. The interview establishes
that invalid dates must fail before records are selected, and archived records stay out.

> A: The export will give you a CSV for the selected date, without archived records. The work covers date validation and file generation; existing records stay unchanged. I will update the existing export Plan and its two Tasks, replacing their earlier export rules and checks. Validation must finish before file generation can use it.
> A: [saves the complete specifications and dependency, then approves the selected subtree once]
> A: `gray_xerinae (dated CSV export)` is saved and approved, ready to build: it will export the selected date without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`. Would you like to see the complete detail?
> U: Yes.
> A: [The saved Plan, any sub-plans and both code Tasks appear in the complete tree with their kinds. All six Plan fields, every Task's context, ordered actions and verification commands, completion criteria, the justified dependency and every replaced field are displayed.]

The first message follows complete internal preparation. The writes follow the summary in
the same turn, without waiting for any answer. “Yes” only displays the saved work: no
write follows it.

## No: reorganising a standalone Task

The user invokes Spec on `copper_manatee (dated CSV export)`, an eligible standalone Task
that holds date validation and file generation. The interview resolves its scope.

> A: You will be able to export a day's records as a CSV and receive a clear error for invalid dates. I will group the work under a new export Plan, keep the existing export Task and add a date-validation Task. The current Task's broad instructions will become the file-generation work, using the validation result first. This changes the organisation of the work, with no change to stored records.
> A: [saves every complete specification, attaches the same Task to the new Plan, adds the justified prerequisite, then approves the new Plan]
> A: `gray_xerinae (dated CSV export)` is saved and approved, ready to build: `copper_manatee (dated CSV export)` keeps its identity and planning there, alongside the new validation work. To implement the whole export, run `/nestor-beta:build gray_xerinae target:main`. Would you like to see the complete detail?
> U: No.

The first message already makes the creations, reorganisation and replaced content
understandable. Before any answer, the agent saves every complete specification, attaches
the same Task using `planId`, adds the justified prerequisite and approves the new Plan in
the same turn. It uses the actual returned slug for that new Plan in its closing.
The Task remains a Task; an eligible ordinary Task gains `template: "code"` without
changing its identity. “No” declines the display only; it neither cancels nor conditions
the saved work.

## Direct detail: an autonomous code Task

> U: Use Spec on `brown_turtle (reject invalid export dates)` and show me the full detail directly.
> A: [After resolving any business decisions and compiling the complete work, show the autonomous code Task in its tree, the full context, steps with actions and executable verification commands, completion criteria, dependencies if any, and every replaced field.]
> A: [saves and approves the Task]
> A: `brown_turtle (reject invalid export dates)` is saved and approved, ready to build: it will reject invalid dates before reading records. To implement it, run `/nestor-beta:build brown_turtle target:main`.

The agent asks no detail question and does not offer the detail again after the writes.
After the requested full presentation, it saves and approves that same Task without a
confirmation. Its repository, scheduling, identity and unrelated content stay intact.

## Nine-path static review

For each row, check both the visible review and the complete saved work. In “Yes” and
“No” paths, the first presentation is the short business summary covering objective,
useful result, scope, main deliverables, impacts and essential changes. The writes follow
in the same turn, and the detail offer comes only after their result. For direct detail,
the user's earlier request replaces that offer. No path asks a display question or
permission to save or approve before the writes.

| Entry | Answer to the offer | Shown before writes | Saved work and approval | After the writes | Static review |
| --- | --- | --- | --- | --- | --- |
| Existing Plan | Yes | Summary naming existing work changed, new work if any, replaced rules and dependency effects | Same Plan and all remaining descendants, complete replacements; approve the selected subtree once | Result, build command and offer; Yes displays every specification, typed tree, justified edges and complete changed fields, without a write | Reviewed: no write waits for the answer; complete subtree is retained |
| Existing Plan | No | Same summary | Same complete subtree and dependency data as Yes; approve once | Result, build command and offer; No changes nothing | Reviewed: no full technical listing is imposed or stored data abbreviated |
| Existing Plan | Direct | Full specifications, typed tree, justified edges and complete changed fields | Same complete subtree; approve once | Result and build command, without an offer | Reviewed: no detail question before or after the writes |
| Task reorganised under a new Plan | Yes | Summary explaining the new grouping, retained Task, new work, replaced instructions and dependency effects | New complete Plan, same existing Task attached through `planId`, other complete Tasks and edges; approve Plan once | Result, build command and offer; Yes displays the new Plan and Tasks, retained Task identity, full specifications, typed tree, justified edges and replaced fields, without a write | Reviewed: Task type and identity are preserved |
| Task reorganised under a new Plan | No | Same summary | Same complete Plan, Task specifications and edges as Yes; approve Plan once | Result, build command and offer; No changes nothing | Reviewed: reorganisation is visible without exposing the full specification |
| Task reorganised under a new Plan | Direct | Full new Plan, typed tree, retained Task identity, specifications, justified edges and replaced fields | Same complete Plan and Tasks; approve Plan once | Result and build command, without an offer | Reviewed: no repeated question or Task-to-Plan conversion |
| Autonomous code Task | Yes | Summary naming the Task and explaining replaced behaviour, scope and effects | Same complete Task, with its own repository; approve Task | Result, build command and offer; Yes displays the Task tree, full context, steps, checks, criteria, dependencies and replaced fields, without a write | Reviewed: Task identity and unrelated content are retained |
| Autonomous code Task | No | Same summary | Same complete Task data as Yes; approve Task | Result, build command and offer; No changes nothing | Reviewed: no loss of executable checks or completion criteria |
| Autonomous code Task | Direct | Full Task tree, specification, dependencies and replaced fields | Same complete Task; approve Task | Result and build command, without an offer | Reviewed: no detail question before or after the writes |

This matrix records static review of the nine documented combinations. It is not a
measurement or a claim that nine conversational sessions have been executed.

## Exceptions at any detail level

> U: Keep it as a draft.
> A: [summary and essential changes]
> A: [saves the complete specification without approving it]
> A: `brown_turtle (reject invalid export dates)` is saved as a draft, not approved: it describes the date-error behaviour for later review. Return to Spec when you want to proceed. Would you like to see the complete detail?

Save the complete specification right after the summary; do not approve it. The same
applies to “save it, but approve later”, which closes with “saved, approval postponed”,
whether or not the user asked for the full detail first. Never use the detail offer or
its answer to override an explicit limit.

> U: Stop here.
> A: The export work stops here. We can continue from the date-error decision later.

No write follows an explicit stop received before saving.

## Invariants checked during review

Every Plan and sub-plan keeps all six fields: `objective`, `requirements`, `architecture`,
`dataHandling`, `errorHandling` and `verificationPlan`. Every code Task keeps its complete
`context`, `steps[{action, verification}]` and `doneWhen`, plus justified dependencies.
No child is left to specify later. Completed work is preserved.

The detail offer and its answer change presentation only and never condition a write. Use
the resolved scope and each item's current matched version/ETag pair for writes; reconcile
conflicts once under the skill's rules. Keep types, identities and scheduling. Save all
remaining work before atomic approval; respect draft, stop and later-approval limits.
Inspect readiness only on an explicit request. None of these examples starts a build.
