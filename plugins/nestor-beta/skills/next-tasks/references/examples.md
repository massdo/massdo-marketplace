# Mixed-view examples

These are illustrative examples, not transcripts to replay. Replace the sample ids and
project with confirmed values.

## Read without root filters

```json
{"tool":"list_items","arguments":{"version_hash":"23fe162bd751c24e0","scope":{"mode":"project","projectId":"QYQi"},"view":"active"}}
```

Read every page. A short next-page reference restores the original scope and view:

```json
{"tool":"list_items","arguments":{"version_hash":"23fe162bd751c24e0","cursor":"c1"}}
```

If an ancestor is missing from the collected pages, read its known identity instead of
searching or listing its descendants. Missing full content uses null in `known`:

```json
{"tool":"get_item","arguments":{"version_hash":"23fe162bd751c24e0","scope":{"mode":"project","projectId":"QYQi"},"ref":["5snR"],"known":[null]}}
```

A held complete ancestor uses its own matched version and ETag instead. Batch at most
five and follow any further ancestor relation; a failed reference stays unresolved.

## Skyline: one Plan, its core/API Task

For a complete active result containing the Task and its Plan, even in that order:

- `silver_whitefish (architecture overhaul)` — Plan; progress: in progress; current approval.
  - `scarlet_tiglon (core and public API migration)` — ready to build.

The Task is not a second independent workstream. Its scope remains core/API; the Plan
holds the wider refactoring objective. A zero Task count cannot hide a returned Plan.

## An ancestor outside the view

For a building Task whose sub-plan and root Plan are absent from active results, read
those two ancestors only as context:

- `silver_whitefish (architecture overhaul)` — Plan; context outside the view; progress and approval as returned.
  - `gray_xerinae (API migration)` — sub-plan; context outside the view; progress and approval as returned.
    - `scarlet_tiglon (core and public API migration)` — building.

Do not expand the ancestors' other children. If an ancestor read fails, show the Task's
unresolved parent reference and say the presentation is partial. Do not promote it to an
autonomous Task. The same principle applies to a historical `parentTaskId`, without
inventing a Plan.

## Backlog after an explicit request

> A: No active Task or Plan in Skyline. The backlog holds 2 Tasks; do you want to see it?
> U: Yes.

Only then read it:

```json
{"tool":"list_items","arguments":{"version_hash":"23fe162bd751c24e0","scope":{"mode":"project","projectId":"QYQi"},"view":"backlog"}}
```

The returned Tasks remain visible under contextual ancestors. Label the Task as backlog,
and the Plan as context outside that view; never give the Plan a `backlog` property.
With zero recorded backlog Tasks, say it is empty and ask nothing. With an absent count,
offer it without a number. Never read it just to obtain a count.
