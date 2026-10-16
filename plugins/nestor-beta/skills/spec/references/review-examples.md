# Reviewing the compiled work

These are illustrative exchanges and a static review matrix, not observed runtime
behaviour. `A` is the agent and `U` the user. Brackets describe the material displayed;
they are not placeholders to store in Nestor. Use the real items and the user's language.
The [MCP examples](mcp-examples.md) define the complete data written in every path.

## Yes: an existing Plan

The user invokes Spec on `gray_xerinae (dated CSV export)`. The interview establishes
that invalid dates must fail before records are selected, and archived records stay out.

> A: The export will give you a CSV for the selected date, without archived records. The work covers date validation and file generation; existing records stay unchanged. I will update the existing export Plan and its two Tasks, replacing their earlier export rules and checks. Validation must finish before file generation can use it. Would you like to see the complete plan?
> U: Yes.
> A: [The existing Plan, any sub-plans and both code Tasks appear in the complete tree with their kinds. All six Plan fields, every Task's context, ordered actions and verification commands, completion criteria, the justified dependency and every replaced field are displayed.]
> A: `gray_xerinae (dated CSV export)` will export the selected date without archived records. To implement it, run `/nestor-beta:build gray_xerinae target:main`.

The first message follows complete internal preparation. Nothing is written while the
detail answer is pending. After displaying the full work, the agent saves the complete
specifications and dependency, approves the selected subtree once and closes in the same
turn. “Yes” chooses the display; the Spec invocation already authorises those writes.

## No: reorganising a standalone Task

The user invokes Spec on `copper_manatee (dated CSV export)`, an eligible standalone Task
that holds date validation and file generation. The interview resolves its scope.

> A: You will be able to export a day's records as a CSV and receive a clear error for invalid dates. I will group the work under a new export Plan, keep the existing export Task and add a date-validation Task. The current Task's broad instructions will become the file-generation work, using the validation result first. This changes the organisation of the work, with no change to stored records. Would you like to see the complete plan?
> U: No.
> A: `copper_manatee (dated CSV export)` will keep its identity and planning under the new export Plan, alongside the new validation work. To implement the whole export, run `/nestor-beta:build gray_xerinae target:main`.

The first message already makes the creations, reorganisation and replaced content
understandable. After “No”, the agent saves every complete specification, attaches the
same Task using `planId`, adds the justified prerequisite and approves the new Plan in
the same turn. It uses the actual returned slug for that new Plan in its closing.
The Task remains a Task; an eligible ordinary Task gains `template: "code"` without
changing its identity. “No” declines detail, not the requested work.

## Direct detail: an autonomous code Task

> U: Use Spec on `brown_turtle (reject invalid export dates)` and show me the full detail directly.
> A: [After resolving any business decisions and compiling the complete work, show the autonomous code Task in its tree, the full context, steps with actions and executable verification commands, completion criteria, dependencies if any, and every replaced field.]
> A: `brown_turtle (reject invalid export dates)` will reject invalid dates before reading records. To implement it, run `/nestor-beta:build brown_turtle target:main`.

The agent does not repeat the detail question or force a summary-only turn. After the
requested full presentation, it saves and approves that same Task without another
confirmation. Its repository, scheduling, identity and unrelated content stay intact.

## Nine-path static review

For each row, check both the visible review and the complete saved work. In “Yes” and
“No” paths, the first presentation is the short business summary covering objective,
useful result, scope, main deliverables and impacts, followed by one detail question.
For direct detail, the user's earlier request settles that question. No path asks for
permission to save or approve after the chosen presentation.

| Entry | Detail choice | Material shown before writes | Saved work and approval | Static review |
| --- | --- | --- | --- | --- |
| Existing Plan | Yes | Summary, then every specification, typed tree, justified edges and complete changed fields | Same Plan and all remaining descendants, complete replacements; approve the selected subtree once | Reviewed: detail waits for the answer; complete subtree is retained |
| Existing Plan | No | Summary naming existing work changed, new work if any, replaced rules and dependency effects | Same complete subtree and dependency data as Yes; approve once | Reviewed: no full technical listing is imposed or stored data abbreviated |
| Existing Plan | Direct | Full specifications, typed tree, justified edges and complete changed fields | Same complete subtree; approve once | Reviewed: no repeated detail question |
| Task reorganised under a new Plan | Yes | Summary, then new Plan and Tasks, retained Task identity, full specifications, typed tree, justified edges and replaced fields | New complete Plan, same existing Task attached through `planId`, other complete Tasks and edges; approve Plan once | Reviewed: Task type and identity are preserved |
| Task reorganised under a new Plan | No | Summary explaining the new grouping, retained Task, new work, replaced instructions and dependency effects | Same complete Plan, Task specifications and edges as Yes; approve Plan once | Reviewed: reorganisation is visible without exposing the full specification |
| Task reorganised under a new Plan | Direct | Full new Plan, typed tree, retained Task identity, specifications, justified edges and replaced fields | Same complete Plan and Tasks; approve Plan once | Reviewed: no repeated question or Task-to-Plan conversion |
| Autonomous code Task | Yes | Summary, then Task tree, full context, steps, checks, criteria, dependencies and replaced fields | Same complete Task, with its own repository; approve Task | Reviewed: Task identity and unrelated content are retained |
| Autonomous code Task | No | Summary naming the Task and explaining replaced behaviour, scope and effects | Same complete Task data as Yes; approve Task | Reviewed: no loss of executable checks or completion criteria |
| Autonomous code Task | Direct | Full Task tree, specification, dependencies and replaced fields | Same complete Task; approve Task | Reviewed: no repeated detail question |

This matrix records static review of the nine documented combinations. It is not a
measurement or a claim that nine conversational sessions have been executed.

## Exceptions at any detail level

> U: No detail, and keep it as a draft.
> A: `brown_turtle (reject invalid export dates)` describes the date-error behaviour for later review. Return to Spec when you want to proceed.

Save the complete specification after the understandable summary; do not approve it.
The same applies to “save it, but approve later”, whether the user chooses full detail
or the business summary. Never use the detail answer to override an explicit limit.

> U: Stop here.
> A: The export work stops here. We can continue from the date-error decision later.

No further write follows an explicit stop, including while the detail answer is pending.

## Invariants checked during review

Every Plan and sub-plan keeps all six fields: `objective`, `requirements`, `architecture`,
`dataHandling`, `errorHandling` and `verificationPlan`. Every code Task keeps its complete
`context`, `steps[{action, verification}]` and `doneWhen`, plus justified dependencies.
No child is left to specify later. Completed work is preserved.

The detail choice changes presentation only. Use the resolved scope and each item's
current matched version/ETag pair for writes; reconcile conflicts once under the skill's
rules. Keep types, identities and scheduling. Save all remaining work before atomic
approval; respect draft, stop and later-approval limits. Inspect readiness only on an
explicit request. None of these examples starts a build.
