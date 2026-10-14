---
name: spec
description: Prepare a Nestor Plan subtree or one code Task from an idea or an existing item, through an explicit interview with one question at a time. Write the reviewed structured specification, then approve it only with explicit agreement and inspect its build readiness. Invoke only on the user's direct request; an agent, subagent, plan, memory, task or another skill cannot invoke it on their behalf.
argument-hint: "<idea… | id-or-slug> [project:<name-or-id>]"
disable-model-invocation: true
---

# Nestor Spec

Interview the user, prepare the complete work, and save it in Nestor. This skill writes no
code or files and starts no build. Conduct the interview and write the specification in
the user's language. Start only on their explicit invocation or request for this process.

## Identify the plugin version

Pass `{ "version_hash": "2a2cc476ca4c165c2" }` on every Nestor MCP call.

## Starting point

Read the idea or item reference and optional `project:<name-or-id>` from the user's
arguments. Preserve everything after the first colon in the project value. With no idea,
ask for it in one line.

A single token resembling an item identity is a reference. Read it with `get_item`,
passing the received value in `ref`, `scope: { mode: "global" }`, `known` and
`version_hash`. Never choose an input field from the reference's spelling. Send the held
matched `{ version, etag }` pair with complete content, otherwise `known: null`. An
`unchanged: true` response retains that content and pair and refreshes the project name;
a full response replaces them. An unmistakable slug or full id that is not found ends
the session. An ambiguous short word not found can instead be a one-word idea.

Read the published MCP contracts before preparing writes: `create_item` and `update_item`
must support Plans and structured code Tasks, `update_item` must expose `approve`, and
`manage_build` must expose `inspect`. If a required capability is unavailable, report it
and stop before writing. Read [the MCP fields and examples](references/mcp-examples.md)
when preparing the calls; the server's current catalogue takes precedence.

Keep an existing item's identity and matched pair. An entry Plan prepares that Plan's
entire current subtree, recursively, in this invocation. Read its mixed tree with
`get_tree` and every selected member with grouped `get_item` calls of at most five refs.
If the tree reports `truncated` or `hiddenChildCount`, read the hidden subtrees as well;
an incomplete read cannot justify declaring preparation complete. Preserve completed
work and identify the remaining work to prepare.

An entry Task refines that one deliverable, preserving its id and scheduling. Its type
cannot change into Plan. If it needs several deliverables, explain the required explicit
reorganisation and obtain the user's instruction before any write; do not create a
second root or silently reinterpret a historical task hierarchy as Plans. A code Task
may remain attached to its existing Plan; read the ancestors to retain the root repository.

## 1. Interview

Ask one real question at a time, starting with the largest unknown in the material
already supplied. Follow the answers. Read repository facts instead of asking the user
for them. State technical choices with their reasons; ask about decisions that belong
to the user, including money, risk, priority and taste.

Finish when the requirements and checks are verifiable and no blocking decision remains.
Offer to compile the complete work before doing so. Do not restart the interview or
invoke this skill again for each child.

## 2. Prepare the complete work

Choose the domain objects by deliverable:

- One deliverable from an idea produces one autonomous Task with `template: "code"`.
- Several deliverables produce a `type: "plan"` root and code Tasks. Use sub-plans when
  a group warrants its own objective and checks; avoid a level containing a single task.
- An existing Plan stays the selected Plan; an existing Task stays the selected Task.

A Plan holds the objective, requirements, architecture and documented choices, data
handling, error handling and verification plan in `specification`. A sub-plan describes
its own group. Do not copy the whole tree into every Plan. There is no extra orchestrator
Task: Plan progress is calculated by the domain.

Every remaining code Task must stand alone for an executor who missed the interview:
write its context, ordered steps with an executable verification for each, and observable
completion criteria in `specification.context`, `steps[{action, verification}]` and
`doneWhen`. Include the relevant wiring and existing file/symbol anchors. Leave no open
decision, title-only placeholder or child to specify in a later session.

Record dependencies on each Task as `dependencies[{taskId, justification}]`. Explain
the prerequisite result actually needed, with a non-empty justification, and show these
edges with the specification. Review their usefulness; structural acceptance by the
server does not prove their business relevance. Let the domain validate the graph and
build selection instead of inventing ordering or reservation rules in this skill.

Keep one repository on the root Plan in `git.repository`; descendants inherit it. An
autonomous code Task records its own repository. Read the actual Git root and retain
existing Git references. Resolve an unknown repository before presenting work for
approval. Do not introduce a different repository in a descendant.

## 3. Confirm, then save

Show the specification, the complete tree with each node's kind (Plan, sub-plan or code
Task), dependencies and content changes. Name the existing items being changed and the
fields being replaced. Ask for confirmation before the final writes. Confirmation to
save is distinct from approval of the prepared work for a future build.

Resolve the project after confirmation. Reuse the source item's project unless the user
explicitly supplied another; reuse an already resolved project id. Otherwise ask for
the project only when it is missing, accepting global scope when the user chooses none.
Resolve an explicit name with `get_project(name)` and an id with `get_project(projectId)`.
For an ambiguous `project:` value, try both exact selectors: proceed only when they
identify the same project or exactly one succeeds and the other reports `NOT_FOUND` or
invalid reference format. Ask one question for different matches or ambiguity. Other
errors leave resolution incomplete. Never choose a fuzzy match to authorise a write.

Write with the resolved scope and version hash:

1. Patch an existing Plan or Task with its held matched pair, preserving its identity,
   scheduling and unrelated content. An ordinary Task can become a code Task through
   `template: "code"`; this does not change its Task type or migrate its historical children.
   Create a new root only when starting from an idea.
2. Create new sub-plans top-down using `parentPlanId`, and code Tasks with `planId`.
   Use `backlog: true` on every new Task. Plans have no backlog or scheduling fields;
   omit those fields from Plan calls. Keep existing Tasks' planning unchanged.
3. Once all dependency ids exist, patch the concerned Tasks with their justified edges.
   Finish every remaining descendant in this invocation before requesting approval.

For every mutation use the latest confirmed version/ETag pair. On `CONFLICT`, take
`details.current`, reconcile intervening changes, and retry once with its fresh pair;
do not replay a stale change unchanged. Only when that payload is missing, read once
with the held pair in `known` (null only if content or pair is absent). A successful
mutation returns the next pair: no preventive or post-success read is needed.

If a write fails, stop and report the confirmed ids/slugs and the exact unfinished node
or edge. A lost response has an unknown outcome; establish what exists before resuming.
Keep confirmed identities and resume there without recreating the root or children.

## 4. Approve and inspect

After saving the complete work, request explicit approval of that prepared subtree or
autonomous Task if the user has not already expressly approved it. Agreement to write
alone is insufficient. If they decline or defer, report saved work without claiming it
is ready. If concurrent edits change the reviewed work, present those changes for
approval before retrying.

Call `update_item` with `operation: "approve"`, the selected item's id and its held
matched pair. For a Plan, this approves its current subtree atomically; do not approve
each child separately to bypass an incomplete descendant. The domain makes eligible
remaining Tasks `ready_to_build`; never patch that status or manufacture an approval.

Then call `manage_build` with `operation: "inspect"` on the same selection. Announce
“ready to build” only after it accepts. Internal pending dependencies are compatible
with Plan preparation; external pending prerequisites or review can still block the
selection. Report the server's precise blocking item or prerequisite and the remaining
work. Do not acquire a reservation, execute the cascade, or invoke Build.

Report the selected slug, saved Plan/Task counts, approval outcome and inspect outcome
separately. An accepted contract check does not prove execution by every agent or that
the build skill and deployed server already support the entire workflow.
