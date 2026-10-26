# Mixed-view examples

These are illustrative examples, not transcripts to replay. Replace the sample ids and
project with confirmed values.

## Read without root filters

```json
{"tool":"list_items","arguments":{"version_hash":"279081db6cfc07f33","scope":{"mode":"project","projectId":"QYQi"},"view":"active"}}
```

Read every page. A short next-page reference restores the original scope and view:

```json
{"tool":"list_items","arguments":{"version_hash":"279081db6cfc07f33","cursor":"c1"}}
```

If an ancestor is missing from the collected pages, read its known identity instead of
searching or listing its descendants. Missing full content uses null in `known`:

```json
{"tool":"get_item","arguments":{"version_hash":"279081db6cfc07f33","scope":{"mode":"project","projectId":"QYQi"},"ref":["5snR"],"known":[null]}}
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
{"tool":"list_items","arguments":{"version_hash":"279081db6cfc07f33","scope":{"mode":"project","projectId":"QYQi"},"view":"backlog"}}
```

The returned Tasks remain visible under contextual ancestors. Label the Task as backlog,
and the Plan as context outside that view; never give the Plan a `backlog` property.
With zero recorded backlog Tasks, say it is empty and ask nothing. With an absent count,
offer it without a number. Never read it just to obtain a count.
