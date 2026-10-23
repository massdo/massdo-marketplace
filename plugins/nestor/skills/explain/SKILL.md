---
name: explain
description: Explain raw text, one Nestor item or one Nestor project as a bespoke, discardable explainer, in the formats the user picks before any work starts, text, an HTML page that mixes text and diagrams, or a video, replaced by a storytelling script when nothing can render one. Run only after a direct user invocation, such as /nestor:explain or $nestor:explain; never invoke it autonomously.
argument-hint: "<text to explain | item id or slug | project name>"
disable-model-invocation: true
---

# Nestor Explain

Reading something is not understanding it. This skill takes one subject, raw text, one
Nestor item or one Nestor project, and turns it into a bespoke, discardable explainer in the formats the user
picks first: text, an HTML page that mixes text and diagrams, or a video, replaced by a
storytelling script when nothing here can render one. The explainer is for
understanding; nothing of it goes back into the journal.

Read journal data through the Nestor MCP server only. Never read a SQLite file or an
export. Write nothing in the journal: no task, no note, no status change, whatever the
explainer shows.

## Identify the plugin version

Pass `{ "version_hash": "10d15cff38fabeb39" }` on every Nestor MCP call.

## Argument

The argument is the text written after the skill name when it is invoked. Depending on
the client, it may arrive in a final `ARGUMENTS: …` line. For an equivalent request in
natural language, read it from the user's message. It is one of two things:

- **A reference**: a single token, or one quoted string, that names a Nestor project or
  an item: a project name such as `lisbon-trip` or `"my long name"`, an item id, an id
  prefix or a slug such as `brown_turtle`. The subject is that project or that item.
- **Raw text**: anything else, taken as is. The subject is that text, nothing more. Do
  not look items or projects up inside it.

An empty argument is an error: say in one line that the skill needs text to explain, an
item reference or a project name, and stop. The argument never carries a format: the
formats are asked below, every time.

## Ask for the formats first

Before any read, any reasoning about the subject and any writing, ask the user which
formats they want, and wait for the answer. Offer exactly these three, and let the user
pick several:

- `text`: the explainer as a reply.
- `html`: one page that mixes the text and its diagrams.
- `video`: a rendered video when a tool here can make one; a storytelling script
  otherwise.

Use the client's question tool when it has one, with multiple selection; otherwise ask
in one short chat message that lists the three options, then end the turn and wait. Never
guess, never default, never skip the question because the subject is short or the user
seems in a hurry.

An answer outside these three options is an error: say in one line which answers are
valid, produce nothing, and stop. An empty answer produces nothing either.

## Read the subject

**Raw text.** No MCP call. Explain the text the user gave, in the user's language.

**A reference.** Resolve it in two exact reads, and stop at the first hit. Project names
are unique in Nestor, so `get_project { name }` with the token resolves a project or
returns `NOT_FOUND`; never fall back to `search_project` to guess one. On `NOT_FOUND`,
call `get_item` with the token in `ref`, the global `scope`, `known` and
`version_hash`. Send the matched `{ version, etag }` pair when the necessary item
content is held; otherwise send `known: null`. With `unchanged: true`, keep the held
content and pair and refresh the project name; a full response replaces them. Never omit
`known` or use null to re-read held content with its pair. Global scope reaches every
item that belongs to no project or to a live project; when this read fails too, say in
one line that the reference matches no project and no item, and stop. On `AMBIGUOUS`,
list the candidate ids and stop.

**A project.** Keep the returned `context` when there is one: it is the project's own
account of itself. Then two calls with the project scope:

- `get_tree` with `views: ["active", "backlog", "completed", "notes"]`, `depth: 6` and
  `verbose: true`. The explainer needs the wording of the items, so titles are not
  optional here. The first line of the server's text states the scope, the views, the
  depth, the item count and `truncated` when the read was incomplete.
- `list_items` with `view: "active"`, `sort: "updated_desc"`, `limit: 10` and
  `includeTags: true`. Its `taskViewCounts` are the numbers behind "where it stands",
  and its page is what moved last.

**An item.** Add, with the item's project scope, or global when it has none:

- `get_tree` with `rootItemId` set to the item's id, `depth: 6` and `verbose: true`,
  when the item is a task. The branch under it is the shape of the work. Views do not
  apply to a rooted tree.
- `item_history { id, operation: "list_snapshots" }`, first page only. The snapshot
  headers are the item's timeline.

An incomplete read, `hasMore: true` or `truncated`, is stated in the explainer itself,
where the reader would otherwise trust a partial picture. Never page further on your
own.

## Say what matters

Whatever the format, the explainer answers these questions, in this order, and skips a
question the subject does not answer rather than inventing one:

1. **What it is.** The subject in one paragraph: its goal for a project or an item,
   its point for a text. A project's goal comes from its `context`, or from its root
   items when it has none.
2. **Where it stands.** For a project, the counts by status and the dates that bite:
   overdue, due today, due this week. For an item, the status, the dates that bite, the
   last changes. For a text, the facts it rests on. Numbers go in a short table or on
   their own line, never inside a sentence.
3. **What matters.** The two or three things the reader must keep.
4. **What waits.** What blocks, what is missing, what the subject leaves open or
   contradicts.
5. **What comes next.** The first actions, in order.
6. **The shape.** How the parts hang together: a hierarchy, a sequence, a dependency.
   This is the diagram when there is one.

Every Nestor item the explainer names carries its slug, so the reader can address it
next. In prose, cite it in one inline-code span: the slug followed by its short
description in parentheses. In a page, show the slug beside the title.

Never state a fact the subject or the reads did not give: no goal, blocker, date or
progress that is absent from them. Say when the subject does not answer a question.

## Write most of the way to ASD-STE100

The prose of every format, captions, page copy and narration included, follows a
controlled style: most of the way to ASD-STE100, because the full specification is stiff
and these rules are the ones that make text readable.

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

## Deliver the formats

Deliver every picked format, in this order: `text`, then `html`, then `video`. Each one
is complete on its own; the page does not replace the text, and the script does not
replace the page.

**`text`.** The explainer is the reply, with the six questions as sections. Add nothing
after it.

**`html`.** One self-contained file: inline CSS and JavaScript, no build step, no
framework required, a library from a public CDN only when it earns its place. The page
carries the six questions as sections, with a navigation that jumps to each, and a
diagram wherever a picture beats a paragraph: the shape as a collapsible tree or an
inline SVG, the timeline as a line, the status as a board. Every diagram has a title and
a caption of three to five sentences. The page is readable in light and dark, at phone
width and on a desktop, and states the subject, the read date and any incomplete read at
the top.

Build it in one pass. A page that opens and reads well is finished: do not iterate on
pixels, screenshots or palettes, the reader wants the picture now, not a polished one in
ten minutes.

Show it the way the client allows. Publish or display it through the client's page tool
when it has one. Otherwise write one file in a temporary directory, open it in the user's
browser when a shell can, and give the path. Never write the file inside the user's
repository or project unless the user asks, and never commit it. The page is discardable:
each invocation builds a fresh one, nothing is saved in the journal, and nothing in it is
a record.

**`video`.** With a tool in this session that renders video and narration, make the
video: one scene per question, narrated in full sentences. Without one, write the
storytelling instead: the explainer told as a story in numbered scenes, each with its
narration in full sentences, what is on screen, and its length. Deliver it as text in the
reply, and name the missing tool in the closing line. Never pretend a video exists, and
never install or sign up for anything to make one.

## After the explainer

When `text` is the only format, add nothing after it. Otherwise close with one line: the
subject, the reads made and the ones left incomplete, the formats delivered and, for
`video`, whether a storytelling replaced it and why. Do not summarise the explainer in
prose; the reader has it.

When the user then asks about one item, call `get_item` with that id or slug in `ref`,
the resolved `scope`, `known` and `version_hash`, under the conditional-read rules above.
A tree or a list alone supplies no matched pair, so send `known: null` unless the
necessary content and pair are held from another response. An explainer never becomes a journal write on
its own: a task or a note the user wants from it is a new, explicit request.
