---
name: explain
description: Explain a Nestor project, a task, a note, or the journal as it stands, as a bespoke and discardable explainer in the richest format the client can show, from controlled plain writing to a diagram or an interactive web page, with a video on request when the tools exist. Run only after a direct user invocation, such as /nestor:explain or $nestor:explain; never invoke it autonomously.
argument-hint: "[project] [format] [focus…] — or project:x item:id format:text|diagram|html|video"
disable-model-invocation: true
---

# Nestor Explain

A list says what is in a project. An explainer says what is going on and what matters, in
a form the reader takes in at a glance. This skill reads one Nestor subject and turns it
into a bespoke, discardable explainer, in the richest format the client can show:
controlled plain writing, then a diagram, then an interactive web page, then a video when
the user asks for one and the tools exist. The explainer is for understanding; nothing of
it goes back into the journal.

Read the data through the Nestor MCP server. Never read a SQLite file or an export.
Write nothing in the journal: no task, no note, no status change, whatever the explainer
shows.

## Identify the plugin version

Pass `{ "version_hash": "10d15cff38fabeb39" }` on every Nestor MCP call.

## Arguments

The arguments are the text written after the skill name when it is invoked. Depending on
the client, they may arrive in a final `ARGUMENTS: …` line. For an equivalent request in
natural language, read them from the user's message. Parse them yourself, and accept two
forms.

**Named** — `key:value`, in any order, any subset:

```
/nestor:explain project:lisbon-trip format:html
/nestor:explain item:azd23 format:diagram
/nestor:explain project:"my long name" what blocks the departure
```

**Positional** — `project`, then `format`. Whatever remains is the `focus`:

```
/nestor:explain lisbon-trip
/nestor:explain lisbon-trip diagram
/nestor:explain lisbon-trip html what blocks the departure
```

`item` has no positional form. An id and a project name look alike, and an explainer of
the wrong thing is worse than a refusal. With `item` given, the first positional token is
the `format`.

A missing parameter keeps its default. Empty arguments mean no parameter was given, so
every default applies and the subject is the journal as it stands. Never ask the user for
a parameter that has a default.

| Parameter | Default | Meaning                                                           |
| --------- | ------- | ----------------------------------------------------------------- |
| `project` | none    | Project name. Resolved through the MCP, see below.                 |
| `item`    | none    | Item id or slug, named form only. Explains that task or note.      |
| `format`  | `auto`  | `text`, `diagram`, `html`, `video` or `auto`. See "Climb the ladder". |
| `focus`   | none    | Free text: the question the explainer answers first.               |

Parsing rules, so that the same input always gives the same explainer:

- Read `key:value` tokens first. What remains is positional, in the order above.
- The five format words are reserved: a positional token equal to one of them is the
  `format`, never a project name, so `/nestor:explain html` is the journal as a page. A
  project that carries one of those names needs the named form.
- A quoted value keeps its spaces: `project:"my long name"`. Without quotes, read the
  value up to the next `key:` token.
- An unknown or repeated key stops the run. Name the offending key and list the four
  valid ones, rather than guessing and explaining the wrong thing.
- A `format` outside the five values stops the run and lists them.

## Resolve the subject

Project names are unique in Nestor, so a name resolves to at most one project.

1. `project` given → `get_project { name }`. Use the returned id as the scope. Keep the
   returned `context` when there is one: it is the project's own account of itself.
2. Unknown name → `search_project { query: name }`, page through `hasMore`, then show the
   close matches and ask which one, a lone match included. Call it with `archived: true`
   too before concluding a name does not exist.
3. `item` given → `get_item` with `ref: item`, the global `scope`, `known` and
   `version_hash`. Send the matched `{ version, etag }` pair when the necessary item
   content is held; otherwise send `known: null`. With `unchanged: true`, keep the held
   content and pair and refresh the project name; a full response replaces them. Never
   omit `known` or use null to re-read held content with its pair. Global scope reaches
   every item that belongs to no project or to a live project. It fails only for an
   archived project: on `NOT_FOUND`, ask for the project name and retry in project scope.
   When `project` is given too, read in that project's scope directly.
4. Neither → the subject is the journal as it stands, in global scope.

## Read what the explainer needs

Read first, then write. Every call below is a read; none of them changes anything.

**A project.** Two calls:

- `get_tree` with the project scope, `views: ["active", "backlog", "completed", "notes"]`,
  `depth: 6` and `verbose: true`. The explainer needs the wording of the items, so
  titles are not optional here. The first line of the server's text states the scope,
  the views, the depth, the item count and `truncated` when the read was incomplete.
- `list_items` with the project scope, `view: "active"`, `sort: "updated_desc"`,
  `limit: 10` and `includeTags: true`. Its `taskViewCounts` are the numbers behind
  "where it stands", and its page is what moved last.

**A task or a note.** The `get_item` response holds the title, the body, the status, the
dates, the tags and the relations. Add:

- `get_tree` with the item's project scope, or global when it has none, `rootItemId` set
  to the item's id, `depth: 6` and `verbose: true`, when the item is a task. The branch
  under it is the shape of the work. Views do not apply to a rooted tree.
- `item_history { id, operation: "list_snapshots" }` with the same scope, first page
  only. The snapshot headers are the item's timeline.

**The journal as it stands.** One call: `list_items` with the global scope,
`views: ["today", "active", "notes"]`, `sort: "updated_desc"`, `limit: 20` and
`includeTags: true`. `taskViewCounts` are the numbers across the journal; the pages are
what is due today, what is moving and what was noted last.

An incomplete read, `hasMore: true` or `truncated`, is stated in the explainer itself,
where the reader would otherwise trust a partial picture. Never page further on your own:
a second page doubles the cost of a picture that is already honest about its edge.

A project with no item, or an empty journal, gets one line saying so, and no artifact.

## Climb the ladder

Each format is easier to take in than the one before it, so `auto` climbs as high as the
client can show:

| Rung      | Pick it when                                                                  |
| --------- | ----------------------------------------------------------------------------- |
| `text`    | Always possible. This is the floor.                                           |
| `diagram` | The client renders Markdown, so a fenced Mermaid block becomes a picture. In a plain terminal, draw ASCII instead. |
| `html`    | You can show a web page: a tool that publishes or displays a page, a browser pane, or a shell that writes a file and opens it in the user's browser. |
| `video`   | Never by `auto`. Only on `format:video`, and only with a tool in this session that renders video and narration. |

A requested rung you cannot show falls back to the highest one you can, and the closing
line says so. A requested rung below the ceiling is honoured as is: a user who asks for
`text` wants text.

`format:video` without a video tool writes the storyboard instead: numbered scenes, the
narration of each one in full sentences, what is on screen, and its length. Deliver it as
an `html` page when you can show one, as `text` otherwise, and name the missing tool in
the closing line. Never pretend a video exists, and never install or sign up for anything
to make one.

## Say what matters

Whatever the rung, the explainer answers these questions, in this order, and leads with
the `focus` when the user gave one:

1. **What it is for.** The goal, in one paragraph, taken from the project `context`, the
   item body, or the root items when nothing else states it. When nothing states it, say
   so rather than inventing one.
2. **Where it stands.** The counts by status, and the dates that bite: overdue, due
   today, due this week. Numbers go in a short table or on their own line, never inside
   a sentence.
3. **What is moving.** The tasks in progress or in review, and what changed last.
4. **What waits.** Unscheduled work, backlog, reviews nobody has taken, and whatever the
   bodies or notes name as a blocker.
5. **What comes next.** The first few tasks to do, by urgency and date, so the reader
   knows where to start.
6. **The shape.** Which task owns which, from the tree. This is the diagram when there is
   one.

Every item the explainer names carries its slug, so the reader can address it next. In
prose, cite it in one inline-code span: the slug followed by its short description in
parentheses. In a diagram or a page, show the slug beside the title.

Never state a fact the reads did not return: no goal, blocker, date or progress that is
absent from a response. Say when the data does not answer a question.

## Write most of the way to ASD-STE100

The prose of every rung, captions and page copy included, follows a controlled style:
most of the way to ASD-STE100, because the full specification is stiff and these rules
are the ones that make text readable.

- One idea per sentence, 20 words at most. A long sentence almost always hides two ideas.
- One topic per paragraph, six sentences at most.
- Active voice, present tense. "The review blocks the release", not "the release is
  blocked by the review".
- One word per concept, kept throughout. Never "task", then "ticket", then "item" for the
  same thing.
- Imperative for actions. "Review `brown_turtle (API draft)`", not "it would be good to
  review".
- Complete sentences, articles kept. A telegraphic fragment saves words and costs
  precision.
- The conversation's language for the prose. Slugs, statuses and tags stay exactly as the
  server spells them.

## Draw the diagram

One diagram, of the kind that fits the question:

- A **tree** for the shape of a project or a branch: one node per task, the slug in the
  node, the status as a class or a colour.
- A **timeline** for an item's history or a project's dates.
- A **board** with one column per status for where things stand.

Title it, add a legend when colours or symbols carry meaning, and put a caption of three
to five sentences under it that says what the picture shows. In a plain terminal, draw
the same structure in ASCII inside a fenced block. More than about forty nodes is noise:
cut at the depth where the shape stays readable, say how many items the cut hides, and
let the user ask for one branch with `item:`.

## Build the page

The `html` rung is one self-contained file: inline CSS and JavaScript, no build step,
no framework required, a library from a public CDN only when it earns its place. Make it
something a person wants to look at, not a list with a stylesheet:

- The six questions as sections, the `focus` first, with a navigation that jumps to each.
- A board with one column per status; each card shows the title, the slug, the due date,
  the priority and the tags.
- The hierarchy as a collapsible tree, every node with its slug.
- A timeline when history was read.
- A filter by status and tag, a search box, and a click on a slug that copies it.
- Readable in light and dark, at phone width and on a desktop.
- The subject, the read date and any incomplete read stated at the top.

Build it in one pass. A page that opens and reads well is finished: do not iterate on
pixels, screenshots or palettes, the reader wants the picture now, not a polished one in
ten minutes.

Show it the way the client allows. Publish or display it through the client's page tool
when it has one. Otherwise write one file in a temporary directory, open it in the user's
browser when a shell can, and give the path. Never write the file inside the user's
repository or project unless the user asks, and never commit it. The page is discardable:
each invocation builds a fresh one, nothing is saved in the journal, and nothing in it is
a record.

## After the explainer

For `text`, the explainer is the reply: add nothing after it. For the other rungs, close
with one line: the subject and the views read, the rung used and, when you fell back,
why, and the reads left incomplete. Do not summarise the explainer in prose; the reader
has it.

When the user then asks about one item, call `get_item` with that id or slug in `ref`,
the resolved `scope`, `known` and `version_hash`, under the conditional-read rules above.
A tree or a list alone supplies no matched pair, so send `known: null` unless the
necessary content and pair are held from another response. An explainer never becomes a
journal write on its own: a task or a note the user wants from it is a new, explicit
request.
