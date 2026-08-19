---
name: tree
description: Render an ASCII tree of a Nestor project's tasks and notes, grouped by status then by parent-child hierarchy. Use it whenever someone wants to see the shape of a project rather than a flat list — asking for an overview, a map, a tree, a structure, the hierarchy of tasks, what hangs under a given task, or how a project is organised. Also use it when the request names a project and asks "where are we" or "what hangs under this task", in any language. Prefer this skill over a plain list whenever parent-child relationships or per-status grouping carry the answer.
---

# Nestor Tree

Render one Nestor project as an ASCII tree. A flat list hides which task owns which
subtask. A tree shows it at a glance, which is the whole point of this skill.

Read the data through the Nestor MCP server. Never read a SQLite file or an export.

## Identify the plugin version

Pass `{ "version_hash": "2995a679105fea81" }` on every Nestor MCP call.

## Arguments

The harness passes the raw argument string. Parse it yourself, and accept two forms.

**Named** — `key:value`, in any order, any subset:

```
/nestor:tree project:nestor-ai view:today level:2
/nestor:tree project:nestor-ai verbose:true
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
| `verbose` | `false`  | `true` adds every title. See "Titles are opt-in" below.      |

Parsing rules, so that the same input always gives the same tree:

- Read `key:value` tokens first. What remains is positional, in the order above.
- A quoted value keeps its spaces: `project:"my long name"`. Without quotes, read the
  value up to the next `key:` token.
- An unknown or repeated key stops the run. Name the offending key and list the five
  valid ones, rather than guessing and rendering the wrong tree.
- A `level` below 1 or above 6, or not an integer, falls back to 3 and says so in the
  closing line.
- `verbose` accepts `true` and `false` only. Anything else stops the run.

## Titles are opt-in

By default the server renders each item as `id  slug`, with no title. That is the shape to
prefer: it answers "what is the shape of this project" and "which item do I address next"
in a fraction of the tokens.

Pass `verbose:true` only when the request needs the wording of the items — the user asks
what a task is about, looks for an item by its name, or wants to read the project rather
than navigate it. `verbose` is also the right choice when the user names no project and is
exploring.

Never pass `verbose:true` "just in case". A tree the user then re-reads with titles costs
two calls; a tree that never needed them costs one.

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
`+` to widen the answer, and pass them to `get_tree` as `views`:

```
/nestor:tree nestor-ai active+notes
/nestor:tree nestor-ai active+backlog+completed
```

When the user asks for the whole project rather than current work, use
`active+backlog+completed+notes` and say so in the closing line. Adding `notes` by
default is right for an overview: a tree without its notes looks complete while it is not.

**`notes` carries no hierarchy.** Notes do not have a parent task — they arrive without
one. A note is rendered under the task it documents, or in the final `NOTES` group when
that task is absent from the tree.

## Ask for the tree

Call `get_tree` once with the scope, the views, the depth, the optional rootItemId, and
`verbose` when titles are needed.

The server returns the finished tree as text. It groups the tasks by status, draws the
hierarchy, picks the tags and the dates, and aligns the columns. **Print that text
unchanged, in a fenced code block.** Do not re-sort it, do not re-align it, do not drop
or add a line. Two calls on unchanged data return the same text.

**Depth.** Pass `level` to the server as `depth`. The server cuts the tree there and marks
each cut branch with `+N` in a left gutter, where `N` counts the direct children it hid.

**Titles.** Pass `verbose` straight through. Omitted, the server sends `id  slug` per line.

**Rooted on an item.** When `item` is given, pass it to the server as `rootItemId`. Do not
start from the project roots: the user asked for one branch, not a map. Views do not apply
in this mode — the server returns the whole branch whatever the status of its tasks, so
`item` on a completed task works. Say in the closing line that `view` was ignored, when
the user passed one.

## After the tree

The first line of the server's answer already states the scope, the views, the depth, the
item count, and `truncated` when the read was incomplete. Do not repeat it.

Add one line only when you have something the server could not know: a `level` you
corrected, or a `view` you ignored because `item` was given. Otherwise say nothing. Do not
summarise the tree in prose; the reader just looked at it.

When you rendered without titles and the user then asks what an item is about, call
`get_item` on that id rather than re-rendering the whole tree with `verbose:true`.
