---
name: tree
description: Render an ASCII tree of a Nestor project's tasks and notes, grouped by status then by parent-child hierarchy. Use it whenever someone wants to see the shape of a project rather than a flat list — asking for an overview, a map, a tree, a structure, the hierarchy of tasks, what hangs under a given task, or how a project is organised. Also use it when the request names a project and asks "where are we" or "what hangs under this task", in any language. Prefer this skill over a plain list whenever parent-child relationships or per-status grouping carry the answer.
---

# Nestor Tree

Render one Nestor project as an ASCII tree. A flat list hides which task owns which
subtask. A tree shows it at a glance, which is the whole point of this skill.

Read the data through the Nestor MCP server. Never read a SQLite file or an export.

## Arguments

The harness passes the raw argument string. Parse it yourself, and accept two forms.

**Named** — `key:value`, in any order, any subset:

```
/nestor:tree project:nestor-ai view:today level:2
/nestor:tree item:azd23
```

**Positional** — `project`, then `view`, then `level`:

```
/nestor:tree nestor-ai active 3
```

`item` has no positional form. An id and a project name look alike, and a tree rooted on
the wrong thing is worse than a refusal.

A missing parameter keeps its default. Never ask the user for a parameter that has one.

| Parameter | Default  | Meaning                                                     |
| --------- | -------- | ----------------------------------------------------------- |
| `project` | none     | Project name. Resolved through the MCP, see below.           |
| `view`    | `active` | One view, or several joined by `+`. See "Choose the views".  |
| `level`   | `3`      | Task depth to render. See "Depth" below.                     |
| `item`    | none     | Item id, named form only. Roots the tree on that item.       |

Parsing rules, so that the same input always gives the same tree:

- Read `key:value` tokens first. What remains is positional, in the order above.
- A quoted value keeps its spaces: `project:"my long name"`. Without quotes, read the
  value up to the next `key:` token.
- An unknown or repeated key stops the run. Name the offending key and list the four
  valid ones, rather than guessing and rendering the wrong tree.
- A `level` below 1 or above 6, or not an integer, falls back to 3 and says so in the
  closing line.

## Resolve the project

Project names are unique in Nestor, so a name resolves to at most one project.

1. `project` given → `get_project { name }`. Use the returned id as the scope.
2. Unknown name → `list_projects`, page through `hasMore`, then show the close matches
   and ask which one. Call it with `archived: true` too before concluding a name does
   not exist.
3. No `project` and no `item` → `list_projects`, then ask which one to render.

**With `item` and no `project`.** Call `get_item` with the global scope. Global scope
reaches every item that belongs to no project or to a live project, so this works in the
normal case. It fails only for an archived project: on `NOT_FOUND`, ask for the project
name and retry in project scope.

## Choose the views

A view holds one kind of item, and each one hides something on purpose:

| View                                 | Holds  | Leaves out                          |
| ------------------------------------ | ------ | ----------------------------------- |
| `active`, `today`, `agenda`, `upcoming`, `inbox` | tasks | notes, backlog, closed states |
| `backlog`                            | tasks  | everything scheduled                |
| `completed`, `cancelled`, `archived`, `trashed` | tasks | live work            |
| `notes`                              | notes  | every task                          |

So `active` alone answers "what is moving", never "show me everything". Join views with
`+` to widen the answer, and pass them to `get_journal_tree` as `views`:

```
/nestor:tree nestor-ai active+notes
/nestor:tree nestor-ai active+backlog+completed
```

When the user asks for the whole project rather than current work, use
`active+backlog+completed+notes` and say so in the closing line. Adding `notes` by
default is right for an overview: a tree without its notes looks complete while it is not.

**`notes` carries no hierarchy.** Notes do not have a parent task — they arrive without
one. When `notes` is the only view, render a flat list in the order the server returned,
and skip the rest of the tree-building rules below. That order is stable across calls, so
two runs on unchanged data render the same list.

## Read the hierarchy

Call `get_journal_tree` once with the scope, views, depth, and optional rootItemId. The
server builds the tree on its side. The response arrives structured.

The result `nodes` is a flat list. Each node carries `depth` (1 for a root, 2 for its
direct child, and so on), `parentTaskId`, and `parentOutsideSelection`. The field
`hiddenChildCount` tells you how many direct children were cut by `depth` — it is `0`
when nothing is cut.

The skill does not paginate anymore; `truncated` signals whether the read was incomplete.

## Build the tree

**Grouping.** A root task goes into the group of its own status, in this order, empty
groups skipped: `in_progress`, `need_review`, `todo`, then `completed` and `cancelled`
when the views carry them. Working states come first because they answer "what is moving".

**Hierarchy wins inside a group.** A subtask is rendered under its parent whatever its
own status, and carries a `[status]` tag when it differs from its group. Moving it to
another group would cut the branch in two, and the branch is the reason for this skill.

**Notes.** The response includes `noteLinks`, a list of relations `{ noteId, taskId, taskRendered }`.
Render a note directly under the task it documents when `taskRendered` is `true`, marked
`(note)`. Notes do not consume a depth level. Every other note goes into the final `NOTES`
group: those whose `taskRendered` is `false`, because the task sits outside the tree or was
cut by `depth`, and those that appear in no `noteLinks` entry at all because they document
nothing.

**Depth.** Pass `level` to the server as `depth`. The server cuts the tree and fills
`hiddenChildCount` with the number of direct children at that level.

**Rooted on an item.** When `item` is given, pass it to the server as `rootItemId`. Do
not start from the project roots: the user asked for one branch, not a map. Views do not
apply in this mode — the server returns the whole branch whatever the status of its tasks,
so `item` on a completed task works. Say in the closing line that `view` was ignored, when
the user passed one.

## Output shape

Keep the id first on every line. It is what the user copies into the next command.

```
nestor-ai · views: active+notes · depth: 3 · 21 items

IN PROGRESS ─────────────────────────────────────────────
  TcSV  Publier Nestor sur le marketplace officiel OpenAI
  ├── 1y5T  Fournir un compte de démonstration sans MFA
  ├── PJdT  Enregistrer la vidéo de démonstration          [todo]
  └── HKTZ  Remplir la fiche et soumettre                  [todo] … +2
  ·── 1BbP  (note) Textes de la fiche publique

TODO ────────────────────────────────────────────────────
  Lyom  Connecter chaque utilisateur au MCP                [urgent] 2026-08-03
  └── E7KJ  Basculer OAuth en production                   [urgent] 2026-08-04
↳ UHWU  Retirer le mode statique du serveur MCP            [high] 2026-08-17

NOTES ───────────────────────────────────────────────────
  MZcJ  Audit externe du 2026-08-05
```

Three markers, each tied to a field in the response:

- `·──` when `noteLinks` holds an entry with `taskRendered: true` for that note.
- `↳` when `parentOutsideSelection` is `true`.
- `… +N` when `hiddenChildCount` is greater than 0; `N` is the number of direct children.

Show `[status]` only when it differs from the group, and priority only when it is `high`
or `urgent`. A tree that repeats `[normal]` on every line stops being readable.

Show one date only: `scheduledAt` when present, `dueAt` otherwise, and mark the second
form with a trailing `!` since a due date is a deadline. A date is either a full day
(`date: "YYYY-MM-DD"` with `isAllDay: true`) or the day part of an instant. Write it as
`YYYY-MM-DD`.

Render the tree in a fenced code block, so terminals and web clients keep the alignment.

## After the tree

Close with one line: the item count, the views rendered, and `truncated` when true. Also
note any `level` that was corrected. Do not summarise the tree in prose; the reader just
looked at it.

Count the nodes you rendered, not `totalCount`. `totalCount` describes the whole selection
before the depth cut, so with `item` it counts branches the reader never saw.
