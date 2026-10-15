# Build MCP calls

These are input-shape examples, not a transcript to replay. Replace the illustrative ids,
version/ETag pairs, evidence and credential with confirmed current values. `4W1R` is a root
Plan, `7TxA` a code Task attached to it. The credential below is fictitious. Do not copy a
real proof into this document or any report. Use the selected object's actual scope.

## Selection and shared Git context

A direct Task request inspects and reserves only that Task; a Plan request uses the Plan
id. The core decides eligibility. An unapproved parent does not invalidate an approved
Task. Pending internal dependencies of a Plan are ordered by the core; a Task's unfinished
prerequisite or an external unfinished dependency refuses startup. Do not duplicate these
policies as plugin text tests.

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"inspect","id":"7TxA"}}
```

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"inspect","id":"4W1R"}}
```

Inspect has no mutation precondition or ownership. Its output contains `target`, `tasks`
and `externalDependencies`, not a new item pair. Read all selected specifications and
external results. Then validate Git. A target branch is stored through `update_item`,
not a `targetBranch` parameter invented for reserve. Only set an absent target before
reservation; repository and target stay frozen while reserved.

```json
{"tool":"update_item","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"patch","id":"4W1R","expectedVersion":3,"expectedEtag":"example-current-etag","patch":{"git":{"targetBranch":"main"}}}}
```

## Reserve and retain ownership

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"reserve","id":"4W1R","expectedVersion":4,"expectedEtag":"example-current-etag"}}
```

Reserve returns `item`, `etag`, `reservation` and private `ownership`.
Only reserve and transfer return the proof. Keep mutation pairs by the response item's
id; the root, selected sub-plan and active Task need their own pairs. Reserve starts the
first eligible Task; read `reservation.taskIds[0]` to confirm its status before editing.
Do not call next before completing it. Once owned, create or reuse the common
branch and record it on the root:

```json
{"tool":"update_item","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"patch","id":"4W1R","expectedVersion":5,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"patch":{"git":{"workBranch":"feat/csv-export","pullRequestUrl":"https://github.com/example/repository/pull/42"}}}}
```

For a direct attached Task, reserve uses `id: "7TxA"`, while Git patches still address
`4W1R`. Reuse the root's existing branch and PR. Do not inspect or approve the parent as
a substitute for the requested Task. A selected sub-plan likewise shares its root's Git
references and reservation context, while next addresses that selected sub-plan.

## Complete only after verified delivery

The example Task declares exactly one criterion, `CSV export is available`, and one step
verification, `pnpm test`. Actual evidence must cover every criterion and command declared
by the real Task. Verify the full pushed SHA and the open common PR before sending:

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"complete","id":"7TxA","expectedVersion":6,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"completionEvidence":{"criteria":[{"criterion":"CSV export is available","result":"Export check produced the expected CSV rows."}],"verifications":[{"command":"pnpm test","result":"12 tests passed; exit 0."}],"commit":{"sha":"0123456789abcdef0123456789abcdef01234567","pushed":true},"pullRequest":{"url":"https://github.com/example/repository/pull/42","state":"open","verified":true}},"review":"none"}}
```

Use `review: "requested"` for required human review; it records need_review and stops the
cascade. `review: "accepted"` requires actual review acceptance, not a skill's assertion.
Completion results and a PR do not establish deployment.

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"next","id":"4W1R","expectedVersion":7,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

For a Plan, next returns the started Task in `item.id` after server rechecks; read it and
continue in the same invocation. A direct Task never advances to siblings. When all work
selected by the invocation is complete, release explicitly. Root Plan completion remains
derived from all its Tasks, even after a direct Task or sub-plan build ends.

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"release","id":"4W1R","expectedVersion":8,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

## Interruption, blockage and transfer alternatives

These calls describe alternatives while a reservation is held, not operations following
the release above. Persist an obstacle on the active Task only:

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"block","id":"7TxA","expectedVersion":6,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"blockage":{"reason":"Required fixture is unavailable.","resumeCondition":"The reviewed fixture is present in this checkout."}}}
```

Interruption retains ownership and the reservation. Read current objects and Git state on
continuation; preserve completed Tasks and evidence. When the condition is observed resolved:

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"resume","id":"7TxA","expectedVersion":7,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"conditionResolved":true}}
```

Review corrections without blockage may use `conditionResolved: false`. Do not call resume
on an already unblocked building Task: continue it with the held ownership. No proof means
no right to resume or reserve again. For an explicitly authorised handoff, the current
owner calls transfer; retain the new ownership privately and immediately discard the old:

```json
{"tool":"manage_build","arguments":{"version_hash":"24c3b620b86bf880e","scope":{"mode":"global"},"operation":"transfer","id":"4W1R","expectedVersion":8,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

For stale preconditions, reconcile `CONFLICT.details.current` and retry once using its
matched pair. A refusal writes nothing. Unknown transport outcome requires reconciliation
before repeating any mutation. Never log the real proof while inspecting diagnostics.
