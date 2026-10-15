# Build MCP calls

These are input and response examples, not a transcript to replay. Replace the illustrative ids,
version/ETag pairs, evidence and credential with confirmed current values. `4W1R` is a root
Plan, `7TxA` a code Task attached to it. The credential below is fictitious. Do not copy a
real proof into this document or any report. Use the selected object's actual scope.

## New build: prepare, then reserve

Read the requested object, root Git context and complete Plan subtree when applicable.
Reuse full held specifications, dependencies and evidence; group missing or conditional
reads. Then validate Git and save an absent target on the shared context. A target branch
belongs in `update_item`, not a `targetBranch` parameter invented for reserve. Use its new
pair when context and selection are the same object; repository and target freeze on reserve.
No inspect call is required before or after saving the target.

```json
{"tool":"update_item","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"patch","id":"4W1R","expectedVersion":3,"expectedEtag":"example-current-etag","patch":{"git":{"targetBranch":"main"}}}}
```

The ids have different roles even when some values coincide:

| Request | reserve / next selection | Shared Git context | Active Task |
| --- | --- | --- | --- |
| Autonomous Task | `7TxA` (no next) | `7TxA` | Read the first returned task id |
| Attached Task | `7TxA` (no next) | Root `4W1R` | Read the first returned task id |
| Root Plan | `4W1R` | `4W1R` | Read the first returned task id |
| Sub-plan | `5Sub` | Root `4W1R` | Read the first returned task id |

A direct Task reserves only itself, using its own pair; it reuses the root's Git context
when attached. Its parent Plans need no approval. An autonomous Task uses the same input
shape but owns its own context. For example, an attached Task reserve and response:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"reserve","id":"7TxA","expectedVersion":4,"expectedEtag":"example-task-etag"}}
```

```json
{"tool":"manage_build","result":{"operation":"reserve","item":{"id":"7TxA","type":"task","version":6,"status":"building"},"etag":"example-task-reserved-etag","reservation":{"contextId":"4W1R","selectionId":"7TxA","taskIds":["7TxA"],"executionId":"abcdefghijklmnopqrstuv","acquiredAt":"2026-10-14T10:00:00.000Z"},"ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

A Plan reserves its remaining subtree. In this example, `8TyB` needs `7TxA`'s result. The
server orders that pending internal dependency; never compute an alternative order or skip
a refused member. Use the root id for a root request or the sub-plan id and its own pair:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"reserve","id":"4W1R","expectedVersion":4,"expectedEtag":"example-current-etag"}}
```

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"reserve","id":"5Sub","expectedVersion":4,"expectedEtag":"example-subplan-etag"}}
```

```json
{"tool":"manage_build","result":{"operation":"reserve","item":{"id":"5Sub","type":"plan","version":5},"etag":"example-subplan-reserved-etag","reservation":{"contextId":"4W1R","selectionId":"5Sub","taskIds":["7TxA","8TyB"],"executionId":"abcdefghijklmnopqrstuv","acquiredAt":"2026-10-14T10:00:00.000Z"},"ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

Retain private ownership immediately. Reserve returns `item`, `etag`, `reservation` and
`ownership`, not `tasks`, `externalDependencies` or an `activeTaskId` field. Its item pair
belongs to `item.id`; the root, selection and active Task each need their own matched pair.
Use only `reservation.taskIds` for execution order. Confirm the first Task's status and
reuse or read every returned Task's full specification, dependencies and completion evidence.
One missing object and one freshness check can share `get_item` with `ref: ["7TxA", "8TyB"]`
and `known: [null, { version: 2, etag: "example-held-task-etag" }]`, plus scope and version_hash.

Read required external dependency objects from those declared dependencies and the known
membership, without adding them to the selection. Verify applicable anchors and their
required results in the resolved Git ref, then in the actual checkout, before editing.
Results produced by an earlier internal Task are checked when its dependent becomes active.
Once owned, create or reuse the common branch and record it on the root:

```json
{"tool":"update_item","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"patch","id":"4W1R","expectedVersion":5,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"patch":{"git":{"workBranch":"feat/csv-export","pullRequestUrl":"https://github.com/example/repository/pull/42"}}}}
```

For an autonomous Task, that Git patch addresses the Task instead. Persist a missing branch
and PR recovered from one matching footer together only after reservation succeeds. A direct attached
Task and a selected sub-plan share the root's branch and PR, not an independent PR.

On a reserve refusal, report its code, message and supplied `details.id` / `dependencyId`,
then stop without inspecting automatically, trying another child or patching status. A
completed status is not proof of a prerequisite's result. If missing external evidence or
dead anchors are found before reserve, stop before acquiring it; if a persistent obstacle
is discovered after success, retain ownership and block the active building Task with a
resume condition. A need_review Task stays suspended for authorised review or corrections.

## Complete only after verified delivery

The example Task declares exactly one criterion, `CSV export is available`, and one step
verification, `pnpm test`. Actual evidence must cover every criterion and command declared
by the real Task. Verify the full pushed SHA and the open common PR before sending:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"complete","id":"7TxA","expectedVersion":6,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"completionEvidence":{"criteria":[{"criterion":"CSV export is available","result":"Export check produced the expected CSV rows."}],"verifications":[{"command":"pnpm test","result":"12 tests passed; exit 0."}],"commit":{"sha":"0123456789abcdef0123456789abcdef01234567","pushed":true},"pullRequest":{"url":"https://github.com/example/repository/pull/42","state":"open","verified":true}},"review":"none"}}
```

Use `review: "requested"` for required human review; it records need_review and stops the
cascade. `review: "accepted"` requires actual review acceptance, not a skill's assertion.
Completion results and a PR do not establish deployment.

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"next","id":"4W1R","expectedVersion":7,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

For a Plan, next returns the started Task in `item.id` after server rechecks; read it and
continue in the same invocation. A direct Task never advances to siblings. When all work
selected by the invocation is complete, release explicitly. Root Plan completion remains
derived from all its Tasks, even after a direct Task or sub-plan build ends.

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"release","id":"4W1R","expectedVersion":8,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

## Interruption, blockage and transfer alternatives

These calls describe alternatives while a reservation is held, not operations following
the release above. Persist an obstacle on the active Task only:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"block","id":"7TxA","expectedVersion":6,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"blockage":{"reason":"Required fixture is unavailable.","resumeCondition":"The reviewed fixture is present in this checkout."}}}
```

Interruption retains ownership and the reservation. On continuation, read the selection,
root context and remaining Tasks conditionally and check their shared Git references.
Preserve completed Tasks and evidence; do not reserve again or inspect automatically. If
already complete, explicitly release a retained owned reservation and stop before Git. If
another execution owns it, stop: reads never recover proof or authorise a new reservation.
When a stored blockage's resume condition is observed resolved:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"resume","id":"7TxA","expectedVersion":7,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"},"conditionResolved":true}}
```

Review corrections without blockage may use `conditionResolved: false`. Do not call resume
on an already unblocked building Task: continue it with the held ownership after checking
Git and prerequisites. With no active Task and remaining selected Plan work, use next,
not reserve. A review without explicit acceptance or correction authorisation stays suspended.
No proof means no right to resume or reserve again. For an explicitly authorised handoff, the current
owner calls transfer; retain the new ownership privately and immediately discard the old:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"transfer","id":"4W1R","expectedVersion":8,"expectedEtag":"example-current-etag","ownership":{"executionId":"abcdefghijklmnopqrstuv","proof":"example-private-proof"}}}
```

For stale preconditions, reconcile `CONFLICT.details.current` and retry once using its
matched pair. A refusal writes nothing. Unknown transport outcome requires reconciliation
before repeating any mutation. Never log the real proof while inspecting diagnostics.

## Optional read-only diagnosis

Inspect remains available for a requested consultation or readiness check without starting
work, including Spec. Its `target`, `tasks` and `externalDependencies` do not change an item
pair. These calls are independent diagnostics, not a fresh-build or continuation preamble:

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"inspect","id":"7TxA"}}
```

```json
{"tool":"manage_build","arguments":{"version_hash":"210e5f031242f376f","scope":{"mode":"global"},"operation":"inspect","id":"4W1R"}}
```

## Expected flow matrix and evidence limits

Here, prepare includes full reads, Git/ref checks and saving an absent target; recheck
confirms the active Task, anchors and prerequisite results in the actual checkout. Deliver
means implementation, required checks, push and a verified open shared PR before complete.
Every reserved write uses private ownership and the addressed object's current pair.

| Case | Expected sequence |
| --- | --- |
| New autonomous Task | prepare -> reserve(Task) -> recheck -> deliver -> complete(Task) -> release(Task) |
| New attached Task | prepare root context -> reserve(Task) -> recheck -> deliver to root PR -> complete(Task) -> release(root) |
| Root Plan or sub-plan with internal dependency | prepare -> reserve(selection) -> recheck first server id -> deliver -> complete -> next(selection) -> recheck dependent result -> deliver -> complete -> release(root) |
| Target saved during preparation | update_item(context target) -> reserve(selection), without inspect between them |
| Reserve refusal | report code, message and supplied blocking ids -> stop, without automatic inspect or another child |
| Selection already completed | full reads -> release if retained and owned -> stop before Git; an empty Plan is not a completed selection |
| Review without authorisation | reads -> suspend; an owned reservation remains held |
| Missing external result before reserve | ref check -> stop before acquisition |
| Persistent obstacle after reserve | retain ownership -> block(active building Task, reason, resumeCondition) -> stop |
| Foreign reservation | reads -> stop; only the current owner's authorised transfer can grant ownership |
| Owned building Task, no blockage | conditional reads -> Git/head/PR and prerequisite checks -> continue, without reserve or resume |
| Owned blocked Task | conditional reads -> observe resumeCondition resolved -> Git checks -> resume(Task, true) -> continue |
| Authorised review corrections | conditional reads -> Git checks -> resume(Task, false) -> correct and verify; acceptance is never self-granted |
| Owned Plan with no active Task | conditional reads and Git checks -> next(selection) -> recheck returned Task -> continue |

These are expected sequences checked by static review, not recorded runtime traces. The
new startup removes one mandatory inspect before reserve; saving a target no longer adds
another inspect. Necessary item reads and Git checks remain, so this is not a claim of a
fixed total call count. Schema tests validate documented payloads, not server policy or an
agent's runtime decisions. No token saving has been measured; any token benefit is an
estimate until a separate before/after runtime comparison records calls and token usage.
