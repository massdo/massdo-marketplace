# MCP fields and examples

Use these examples when preparing calls. They describe input shapes, not writes to run
verbatim: replace sample ids, repository, version and ETag with confirmed values. Each
JSON block names the tool and its arguments. Always send this skill's `version_hash`
and the resolved scope. Read the current catalogue if it differs from these examples.

Plans use `type: "plan"`, `parentPlanId` and the Plan specification fields. Code Tasks
use `type: "task"`, `template: "code"`, `planId`, the Task specification fields and
justified dependencies. `parentTaskId` is the historical ordinary Task hierarchy and
does not replace either Plan membership field. Type is immutable.

## Idea with one deliverable

Create an autonomous code Task in the backlog. Its repository belongs to the Task.

```json
{
  "tool": "create_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "type": "task",
    "title": "Reject invalid export dates",
    "template": "code",
    "backlog": true,
    "git": { "repository": "https://github.com/example/project" },
    "specification": {
      "context": "The CSV export accepts an invalid date; reject it before querying records.",
      "steps": [
        { "action": "Validate the export date and test the rejection path.", "verification": "pnpm test -- export-date" }
      ],
      "doneWhen": ["An invalid export date returns the documented validation error."]
    }
  }
}
```

Approve it next, with the pair this creation returned.

## Idea with several deliverables

Create the root Plan first. Plans accept no `backlog`, `scheduledAt` or `template`.
Create a sub-plan with `parentPlanId` when appropriate; its specification fills the same
six fields for that group, and it inherits the root repository.

```json
{
  "tool": "create_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "type": "plan",
    "title": "Export dated records",
    "git": { "repository": "https://github.com/example/project" },
    "specification": {
      "objective": "Export the selected date's records to CSV.",
      "requirements": ["Reject invalid dates.", "Export only records on the selected date."],
      "architecture": "Validate the input in the export use case and serialize its selected records.",
      "dataHandling": "Read existing records; keep no additional persistent data.",
      "errorHandling": "Return the documented validation error before querying an invalid date.",
      "verificationPlan": ["pnpm test -- export-date", "pnpm test -- csv-export"]
    }
  }
}
```

Attach each complete code Task to the returned Plan id. New Tasks carry `backlog: true`;
attached Tasks inherit the repository and need no duplicate Git context. Save dependencies
once all ids are known:

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "id": "5X2T",
    "operation": "patch",
    "expectedVersion": 1,
    "expectedEtag": "0123456789abcdef0123456789abcdef",
    "patch": {
      "dependencies": [{ "taskId": "6Y3U", "justification": "Needs validated dates before selecting records for CSV." }]
    }
  }
}
```

Approve the root Plan once its whole subtree is saved.

## Existing Plan

Read the complete current subtree. `depth` is limited to six; read hidden subtrees until
`truncated` and `hiddenChildCount` no longer leave members unread. Then use `get_item`
for full member content and matched preconditions, including completed work to preserve.

```json
{
  "tool": "get_tree",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "rootItemId": "4W1R",
    "depth": 6,
    "verbose": true
  }
}
```

Patch the existing Plan's structured `specification` without changing its id or parent.
Prepare all remaining sub-plans and code Tasks before approval. Approval uses the latest
pair after all these writes; a child's change can invalidate its ancestor's approval.
An approved Plan keeps its approval until such a saved change: do not reset it first,
and approve the Plan again after the writes.

## Existing Task

Refine the same deliverable. This example specialises a `todo` ordinary Task with no
parent or subtasks, keeping its type and planning. For an attached code Task, keep its `planId`
and inherited repository instead of supplying the autonomous Git context below.

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "id": "5X2T",
    "operation": "patch",
    "expectedVersion": 3,
    "expectedEtag": "0123456789abcdef0123456789abcdef",
    "patch": {
      "template": "code",
      "git": { "repository": "https://github.com/example/project" },
      "specification": {
        "context": "The CSV export accepts an invalid date; reject it before querying records.",
        "steps": [{ "action": "Validate the export date and test the rejection path.", "verification": "pnpm test -- export-date" }],
        "doneWhen": ["An invalid export date returns the documented validation error."]
      }
    }
  }
}
```

An ordinary Task with a parent, children or an incompatible status cannot be converted
to code by this call. Report the domain restriction instead of clearing those fields.

An approved code Task takes only its changed fields, such as this `specification`, without
`template` or `git`. The saved change revokes its approval and that of its ancestor Plans:
approve the Task again, and an ancestor only when its complete subtree is within the
requested scope and prepared. Otherwise report the ancestor's revoked approval.

A standalone Task holding several deliverables keeps its type. Create the root Plan with
the repository first, then attach the Task to it; an attached Task sends no `git`.
Never patch `type` or migrate historical Task children automatically.

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "id": "5X2T",
    "operation": "patch",
    "expectedVersion": 3,
    "expectedEtag": "0123456789abcdef0123456789abcdef",
    "patch": {
      "template": "code",
      "planId": "4W1R",
      "specification": {
        "context": "The CSV export accepts an invalid date; reject it before querying records.",
        "steps": [{ "action": "Validate the export date and test the rejection path.", "verification": "pnpm test -- export-date" }],
        "doneWhen": ["An invalid export date returns the documented validation error."]
      }
    }
  }
}
```

## Approval after saving

Once the complete work is saved, approve the selected Plan's current subtree or the
autonomous Task without a question, using the latest pair:

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "id": "4W1R",
    "operation": "approve",
    "expectedVersion": 4,
    "expectedEtag": "0123456789abcdef0123456789abcdef"
  }
}
```

`approve` accepts no patch. It refuses incomplete work without partially approving the
subtree and names the blocking item in `details.id`: report it with the saved, unapproved
state, then approve again once the missing content is saved, without a validation
question. Use the returned pair directly for another mutation; no verification read is
required. This operation preserves completed work and makes eligible remaining Tasks
`ready_to_build`; it reserves and starts no build.

An explicit draft or later approval sends the same writes without `approve`. An explicit
stop sends no further call.

## Conflicts and failures

A stale pair returns `CONFLICT` with `details.current`, the current item in the
`get_item` format. Reapply the intended change to that state and retry the same operation
once with its `item.version` and `etag`, never with the refused pair or the stale change
as is. Without `details.current`, read the item once with `get_item` and the held pair in
`known`, then retry once. Ask the user first only when the intervening change raises a
decision they have not settled, then resume without a general confirmation. A second
refusal stops: report the confirmed ids and the exact unfinished node or edge.

A failed or lost write keeps the writes confirmed before it. Establish what exists, then
resume from the confirmed identities without creating them again.

## Requested readiness check

Only when the user explicitly asks whether the saved work can be built, inspect it:

```json
{
  "tool": "manage_build",
  "arguments": {
    "version_hash": "2c78218b37686e602",
    "scope": { "mode": "global" },
    "id": "4W1R",
    "operation": "inspect"
  }
}
```

`inspect` writes nothing and needs no ownership proof or mutation precondition. On
refusal, report `details.id` and `details.dependencyId` when supplied. Spec stops at
preparation: it never calls `reserve`, `next` or a build skill.
