---
name: spec
description: Prepare a Nestor Plan subtree or one code Task from an idea or an existing item, through an explicit interview with one question at a time. Once the work is complete, save its structured specification and approve it without asking for a final confirmation, unless the user explicitly asks for a draft, a stop or a later approval. Invoke only on the user's direct request; an agent, subagent, plan, memory, task or another skill cannot invoke it on their behalf.
argument-hint: "<idea… | id-or-slug> [project:<name-or-id>]"
disable-model-invocation: true
---

# Nestor Spec

Interview the user, prepare the complete work, then save and approve it in Nestor. This
skill writes no code or files and starts no build. Conduct the interview and write the
specification in the user's language. Start only on their explicit invocation or request
for this process. That invocation authorises, by default, saving and approving the
requested scope as soon as the work is complete, with nothing displayed before; the full
detail stays available afterwards on request. An explicit request for a draft or a later
approval limits this to saving; an explicit stop ends the session without further writes.
Never ask for approval again to get around that choice.

## Identify the plugin version

Pass `{ "version_hash": "2b4920530586d8360" }` on every Nestor MCP call.

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
must support Plans and structured code Tasks, and `update_item` must expose `approve`.
If a required capability is unavailable, stop before writing and use the closing rule below. Read
[the MCP fields and examples](references/mcp-examples.md) when preparing the calls; the
server's current catalogue takes precedence.

Keep an existing item's identity and matched pair. An entry Plan prepares that Plan's
entire current subtree, recursively, in this invocation. Read its mixed tree with
`get_tree` and every selected member with grouped `get_item` calls of at most five refs.
If the tree reports `truncated` or `hiddenChildCount`, read the hidden subtrees as well;
an incomplete read cannot justify declaring preparation complete. Preserve completed
work and identify the remaining work to prepare. A cancelled, archived or trashed code
Task in the subtree prevents its approval: explain the scope problem before any write and ask the user
for an explicit change of scope.

An entry Task refines that one deliverable, preserving its id and scheduling. Its type
cannot change into Plan, and a historical task hierarchy never becomes Plans implicitly.
For an ordinary Task, read its status and historical hierarchy as well: the server permits
conversion to code only for a `todo` Task with neither parent nor subtasks. If it is
ineligible, explain the reorganisation needed and obtain explicit instructions before
writes, without changing its status or detaching children to force the conversion.
A code Task may remain attached to its existing Plan; read its ancestor Plans to retain
the root repository and their approval state.

When a standalone Task holds several deliverables, prepare a new root Plan in its project
with the Task's repository, then attach the Task to it with `planId` as one of its code
Tasks, converting it with `template: "code"` when it is ordinary. The detail tree shows
this reorganisation; the new Plan then becomes the selection.
Ask the user first when you are less than 95% sure the Task holds several deliverables.
For an attached code Task or an ineligible Task, explain the need and obtain explicit
reorganisation instructions instead.

## 1. Interview

Ask one real question at a time, starting with the largest unknown in the material
already supplied. Follow the answers. Read repository facts instead of asking the user
for them. State technical choices with their reasons; ask about decisions that belong
to the user, including money, risk, priority and taste. Questions serve business and
technical decisions only: never ask a presentation question. Never ask for permission to
compile, save or approve.

Keep every question short and natural, one per decision the user must make. Do not
justify it with this skill's local path, a quoted rule or an account of internal
mechanics. When a higher-priority instruction requires citing the skill, follow it
without expanding the question around it.
[The exchange examples](references/confirmation-examples.md) illustrate this tone and
each closing.

Finish when the requirements and checks are verifiable and no blocking decision remains,
then compile the complete work without asking. Do not restart the interview or invoke
this skill again for each child.

## 2. Prepare the complete work

Choose the domain objects by deliverable:

- One deliverable from an idea produces one autonomous Task with `template: "code"`.
- Several deliverables produce a `type: "plan"` root and code Tasks. Use a sub-plan when
  a group warrants its own specification; avoid a level containing a single task.
- An existing Plan stays the selected Plan; an existing Task stays the selected Task.

A Plan holds the objective, requirements, architecture and documented choices, data
handling, error handling and verification plan in `specification`. Approval requires all
six fields on every Plan, sub-plans included: a sub-plan fills them for its own group.
Do not copy the whole tree into every Plan. There is no extra orchestrator Task: Plan
progress is calculated by the domain.

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
autonomous code Task records its own repository. Record the checkout's `origin` URL in
HTTPS form without `.git`, such as `https://github.com/owner/repo`, never a local path,
and retain existing Git references. Resolve an unknown repository during the interview.
Do not introduce a different repository in a descendant.

Compile all of this internally before saving. What is displayed never shortens the
specification: every Plan, sub-plan, code Task and dependency must be fully prepared and
saved, whatever level of detail is displayed.

## 3. Save, then report the status

Once the work is compiled, save it as described below and approve it under section 4, in
the same turn and without waiting for an answer. Display nothing before these writes: no
summary, no presentation question and no write confirmation, since the invocation already
authorises them. An explicit draft or later approval saves without approving; an explicit
stop received before saving prevents every write.

After the writes, close under the rule below: the status of the saved work, then
« Tape detail pour voir le détail. » Use the equivalent in the user's language. When the
user then answers `detail` or an equivalent, show the saved work without writing again:
every specification, the complete tree with each node's kind (Plan, sub-plan or code
Task), justified dependencies, the existing items changed and the fields replaced. Any
other answer, or none, changes nothing that is saved.

If the user explicitly asked for the detail during the interview, still display nothing
before the writes: put that detail after the status sentence of the closing, without the
`detail` offer. See [the review examples](references/review-examples.md) for the three
entry points and their closings.

Resolve the project during the interview. An existing item keeps its own project, since
the server refuses writes from another one: when `project:` names a different project,
say so and ask whether to continue in the item's project before any write. Reuse an
already resolved project id. An explicit `project:` is authoritative: read no Git to
confirm or replace it. Without `project:`, infer the project of work started from an
idea from the workspace's Git repository:

1. Work from the repository root, not from the current directory — a subdirectory and a
   linked worktree must give the same answer as the root of the reference repository.
2. Read the `origin` remote and keep the last segment of its URL, without a `.git` suffix.
   Recognize the usual HTTPS, SSH and SCP forms, with or without the suffix.
3. With no `origin`, use the name of the repository root directory — never the arbitrary
   directory name of a linked worktree standing in for another project.

Resolve that inferred name with `get_project(name)` only. When Git yields no reliable
name or that read reports `NOT_FOUND`, ask for the project in one question, accepting
global scope when the user chooses none.
Resolve an explicit name with `get_project(name)` and an id with `get_project(projectId)`.
For an ambiguous `project:` value, try both exact selectors: proceed only when they
identify the same project or exactly one succeeds and the other reports `NOT_FOUND` or
invalid reference format. Ask one question for different matches or ambiguity. Other
errors leave resolution incomplete. Never choose a fuzzy match to authorise a write.

Write with the resolved scope and version hash:

1. Patch an existing Plan or Task with its held matched pair, preserving its identity,
   scheduling and unrelated content. A patched `specification` or `dependencies` replaces
   the stored value, so send it complete. An eligible ordinary Task becomes a code Task
   through `template: "code"`; this does not change its Task type. Create a new root only
   from an idea or for a reorganised standalone Task.
2. Create new sub-plans top-down using `parentPlanId`, and code Tasks with `planId`.
   Use `backlog: true` on every new Task. Plans have no backlog or scheduling fields;
   omit those fields from Plan calls. Keep existing Tasks' planning unchanged.
3. Once all dependency ids exist, patch the concerned Tasks with their justified edges.
   Finish every remaining descendant in this invocation before approving.

For every mutation use the latest confirmed version/ETag pair. On `CONFLICT`, take
`details.current`, reconcile intervening changes, and retry once with its fresh pair;
do not replay a stale change unchanged. Only when that payload is missing, read once
with the held pair in `known` (null only if content or pair is absent). A successful
mutation returns the next pair: no preventive or post-success read is needed. When an
intervening change raises a decision the user has not settled, ask that one question,
then resume saving and approving; never replace it with a general confirmation.

If a write fails, stop; retain the confirmed identities and exact unfinished node or edge
for recovery, and use the closing rule below. A lost response has an unknown outcome; establish what exists before resuming.
Keep confirmed identities and resume there without recreating the root or children.
Never turn a blockage into a validation question.

## 4. Approve and close

Once the complete work is saved, approve it without asking, unless the user asked for a
draft or a later approval: then keep the work unapproved. Call `update_item` with
`operation: "approve"`, the selected item's id and its held matched pair. For a Plan,
this approves its current subtree atomically; do not approve each child separately to
bypass an incomplete descendant. The domain makes eligible remaining Tasks
`ready_to_build`; never patch that status or manufacture an approval.

A refusal names the blocking item and field: retain them for recovery and use the closing rule below.
When content is missing, ask only for a decision that belongs to the user, or read the
missing fact from the repository; then save the completion and approve again without a
validation question.

On approved work, never reset an approval at the start of the interview: a saved change
to planned work lets the domain revoke the approval of the changed item and of its
ancestor Plans. Approve the requested scope again after saving. Approve an ancestor again
only when its complete subtree is already within the requested scope and prepared;
otherwise leave the ancestor unapproved, without widening the scope. Its conflict
after your own change is expected and is not a concurrent edit.

Do not inspect or reserve the build afterwards. Pending external prerequisites belong to
build selection and reservation, not to a new validation of the specification. Only when
the user explicitly asks to check build readiness, confirm that the catalogue exposes
`manage_build` with `operation: "inspect"`, call it on the selection and explain its
effect using the closing rule below; it writes nothing. Never acquire a reservation, execute the cascade, or invoke
Build.

## User messages

Close with one short message: cite the selection using Nestor's item citation rule, say
that it is saved and give its actual status in plain words, then add « Tape detail pour
voir le détail. » unless the detail is already shown. The statuses are: ready to build;
draft, not approved; saved, approval postponed. Add no business summary and no build
command. This closing replaces Nestor's per-mutation report. When the project was
inferred from Git rather than named, name it in the status sentence.

When a write fails, say what was not saved or approved and the action needed. Never
present a failure as a success, duplicate work after it or ask for a replacement
validation.

Apply the same rule to intermediate messages, stops, refusals and conflicts: explain the
effect on the user's goal, the affected item and the action or decision needed, without
raw MCP diagnostics or hiding a real problem. A draft remains work to finish; a refusal or
failed write must not imply the work is ready to build. Apart from the status sentence, do
not narrate creation, saving, approval, revocation, inspection, reservation, statuses,
item counts, versions/ETags or technical identifiers beyond the citation. Keep recovery
details in the held state and MCP records. Interview questions retain their existing
rules.
