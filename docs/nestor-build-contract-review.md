# Build contract review

Reviewed against `client.listTools()` on an isolated in-memory Journal server from
`349352dcce0e25d41b5b1a69487ae97e4f1784bb`, including merged Journal PR #126.
No production data or reservation was used. This is a catalogue and source review,
not proof of a deployed server or an agent executing the complete workflow.

The shared fixture `tests/fixtures/nestor-spec-catalog.json` captures four input schemas
and the manage_build output schema, with descriptions removed. All match listTools
exactly. All eleven Build JSON examples are accepted by the actual Journal DTOs.
Only input/output shapes are tested in the plugin; business behavior stays in Journal.

| Operation | Addressed item | Preconditions and observed contract |
| --- | --- | --- |
| inspect | Selected Task or Plan | Read only; returns target, ordered tasks and externalDependencies. |
| reserve | Selected Task or Plan | Held pair, free root context, approved selection and stored target; returns context item/pair, reservation and private ownership. |
| next | Selected Plan | Held pair and ownership; starts a Task and returns that Task in item, with its pair. |
| block | Active Task | Held pair, ownership, reason and resumeCondition; reservation remains. |
| resume | Interrupted Task | Held pair, ownership and conditionResolved; server rechecks remaining work. |
| complete | Active Task | Held pair, ownership and complete evidence for criteria, commands, pushed SHA and open verified PR; review requested suspends progression. |
| release | Root context | Held pair and ownership; completed work remains, eligible unfinished work returns to ready_to_build. |
| transfer | Root context | Held pair and current ownership; returns new ownership, immediately revoking the former proof. |

`activeTaskId` is not an output field. Reserve returns the shared context and its
ordered reservation.taskIds; the skill reads Task status before editing. Next returns
the started Task in item.id. Store each pair against its actual response item. Build
mutations can change other members' ETags; a stale pair follows the conflict contract.

## Reviewed entry and continuation cases

| Case | Skill behavior checked against the contract |
| --- | --- |
| Direct invocation | Empty arguments stop; only the user starts Build. Both clients retain explicit invocation policy. |
| Direct Task | Inspect and reserve only that Task. Parent approval is unnecessary. An unfinished prerequisite or foreign reservation cannot be bypassed. |
| Plan | Read the complete subtree; use inspect/reserve ordering, then complete/next sequentially without another skill invocation or an agent per child. An empty remaining selection stops before Git or reservation. |
| Attached Task or sub-plan | Follow planId/parentPlanId to the root; reuse its repository, target, work branch and PR. A sibling is not implicitly selected. |
| Missing external result | Inspect the intended work ref before reservation, then the actual checkout before editing. Refuse an absent result even for a completed dependency. Never merge or cherry-pick it automatically. |
| Interruption | Keep the reservation and completed evidence. A continuation after the last completion releases the retained owned reservation before Git. Otherwise inspect and resume only a blocked/reviewed Task after resolution; an unblocked building Task continues under its existing ownership. |
| Transfer | A different execution needs an explicit handoff by the owner. Reads cannot recover the proof; the old proof cannot authorise continuation. |
| Review or refusal | Stop the entire loop, including when inspect reports an existing need_review Task anywhere in the selection. Record requested review through complete; never set completed or choose another child to evade the stop. |
| Completion | Verify pushed head and open shared PR before evidence. Release explicitly at the end of the selection. Root completion is derived from all actionable Tasks. |

Repository validation: `python3 scripts/validate_skills.py` passes for 18 skills;
`python3 -m unittest discover -s tests` passes 69 tests; `sh scripts/check.sh --baseline
origin/main --require-release` checks all three plugins, YAML and official manifests.
Use the repository's `.venv/bin` on PATH for the Python commands.

Journal's eight focused build use-case suites pass 32 tests. Its selection, progression
and reservation domain suites pass another 27 tests with Node 24.18.0. These cover the
policies behind the reviewed decisions without reimplementing them in plugin tests.

Integration review remains: execute the prepared Spec-to-Build workflow with a connected
server exposing these contracts and an explicitly approved code Task or Plan. The MCP
tools exposed to this session do not include manage_build. The current delivery updates
the shared PR; it does not reserve or execute a production cascade, deploy or release.
