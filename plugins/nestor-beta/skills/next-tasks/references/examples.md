# Mixed-view examples and contract coverage

These are synthetic documentary examples, not transcripts or proof of agent runtime
behaviour. The tests validate requests and responses against the captured MCP catalogue,
then check that the declared presentation preserves every selected item's identity,
parent, state and order. They do not implement a renderer distributed by this plugin.

## Read without root filters

```json
{"tool":"list_items","arguments":{"version_hash":"2b4920530586d8360","scope":{"mode":"project","projectId":"QYQi"},"view":"active"}}
```

Read every page. A short next-page reference restores the original scope and view:

```json
{"tool":"list_items","arguments":{"version_hash":"2b4920530586d8360","cursor":"c1"}}
```

If an ancestor is missing from the collected pages, read its known identity instead of
searching or listing its descendants. Missing full content uses null in `known`:

```json
{"tool":"get_item","arguments":{"version_hash":"2b4920530586d8360","scope":{"mode":"project","projectId":"QYQi"},"ref":["5snR"],"known":[null]}}
```

A held complete ancestor uses its own matched version and ETag instead. Batch at most
five and follow any further ancestor relation; a failed reference stays unresolved.

## Skyline: one Plan, its core/API Task

For a complete active result containing the Task and its Plan, even in that order:

- `silver_whitefish (refonte de l’architecture)` — Plan; progression : en cours ; approbation courante.
  - `scarlet_tiglon (migration du core et de l’API publique)` — prête à build.

The Task is not a second independent workstream. Its scope remains core/API; the Plan
holds the wider refactoring objective. A zero Task count cannot hide a returned Plan.

## An ancestor outside the view

For a building Task whose sub-plan and root Plan are absent from active results, read
those two ancestors only as context:

- `silver_whitefish (refonte de l’architecture)` — Plan ; contexte hors vue ; progression et approbation renvoyées.
  - `gray_xerinae (migration de l’API)` — sous-plan ; contexte hors vue ; progression et approbation renvoyées.
    - `scarlet_tiglon (migration du core et de l’API publique)` — build en cours.

Do not expand the ancestors' other children. If an ancestor read fails, show the Task's
unresolved parent reference and say the presentation is partial. Do not promote it to an
autonomous Task. The same principle applies to a historical `parentTaskId`, without
inventing a Plan.

## Backlog after an explicit request

> A: Aucune tâche ni aucun Plan actif dans Skyline. Le backlog compte 2 tâches ; veux-tu le voir ?
> U: Oui.

Only then read it:

```json
{"tool":"list_items","arguments":{"version_hash":"2b4920530586d8360","scope":{"mode":"project","projectId":"QYQi"},"view":"backlog"}}
```

The returned Tasks remain visible under contextual ancestors. Label the Task as backlog,
and the Plan as context outside that view; never give the Plan a `backlog` property.
With zero recorded backlog Tasks, say it is empty and ask nothing. With an absent count,
offer it without a number. Never read it just to obtain a count.

## Regression cases

The fixture `tests/fixtures/next-tasks-cases.json` records expected outlines for:

- Skyline Plan/core, ordinary and code autonomous Tasks, Plan/Tasks and nested sub-plans;
- historical Task parents, ancestors outside the view and unresolved ancestor reads;
- ready-to-build/building Tasks, calculated Plan progress and separate approval;
- a Plan alone with zero active Tasks, a genuinely empty mixed view and missing counters;
- parents and children on different pages, server sibling order and an interrupted page;
- an active exchange without any backlog read, and explicitly requested backlog Tasks
  grouped under contextual Plans.

The catalogue snapshot includes its source commit and capture method. Current schemas
require counters; missing-counter cases are explicitly labelled compatibility inputs
that fail that strict schema, not examples of conforming current server output. They
document graceful handling of absent data without changing the captured contract.
All outlines are static expectations, not generated application output or live sessions.
