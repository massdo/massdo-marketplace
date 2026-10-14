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
    "version_hash": "25e71faa2fe3ec161",
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

## Idea with several deliverables

Create the root Plan first. Plans accept no `backlog`, `scheduledAt` or `template`.
Create a sub-plan with `parentPlanId` when appropriate; its specification fills the same
six fields for that group, and it inherits the root repository.

```json
{
  "tool": "create_item",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
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
    "version_hash": "25e71faa2fe3ec161",
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

## Existing Plan

Read the complete current subtree. `depth` is limited to six; read hidden subtrees until
`truncated` and `hiddenChildCount` no longer leave members unread. Then use `get_item`
for full member content and matched preconditions, including completed work to preserve.

```json
{
  "tool": "get_tree",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
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

## Existing Task

Refine the same deliverable. This example specialises a `todo` ordinary Task with no
parent or subtasks, keeping its type and planning. For an attached code Task, keep its `planId`
and inherited repository instead of supplying the autonomous Git context below.

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
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

A standalone Task holding several deliverables keeps its type. Create the root Plan with
the repository first, then attach the Task to it; an attached Task sends no `git`.
Never patch `type` or migrate historical Task children automatically.

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
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

## Explicit approval, then read-only inspection

Confirming persistence alone does not authorise approval. With explicit agreement on
the saved work, approve the selected Plan's current subtree or the autonomous Task:

```json
{
  "tool": "update_item",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
    "scope": { "mode": "global" },
    "id": "4W1R",
    "operation": "approve",
    "expectedVersion": 4,
    "expectedEtag": "0123456789abcdef0123456789abcdef"
  }
}
```

`approve` accepts no patch. It refuses incomplete work without partially approving the
subtree. Use the confirmation's pair directly for another mutation; no verification read
is required. This operation preserves completed work and makes eligible remaining Tasks
`ready_to_build`. Other accepted states, such as `need_review`, can still prevent readiness.

```json
{
  "tool": "manage_build",
  "arguments": {
    "version_hash": "25e71faa2fe3ec161",
    "scope": { "mode": "global" },
    "id": "4W1R",
    "operation": "inspect"
  }
}
```

`inspect` writes nothing and needs no ownership proof or mutation precondition. Its
acceptance is required before reporting build readiness. A pending internal dependency
can be selected before its dependent Task in a Plan; an external prerequisite must already
be completed. On refusal, report `details.id` and `details.dependencyId` when supplied.
Spec stops at preparation: it never calls `reserve`, `next` or a build skill.
