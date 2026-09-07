---
name: spec
description: Turn a raw idea into a Nestor task tree, one question at a time. Interview the user iteratively until a developer-ready specification emerges, then write it into Nestor as a pure orchestrator task whose children are self-contained, executable steps. Invoke this skill only after a direct user action such as /nestor-beta:spec with an idea. An agent, subagent, plan, memory, Nestor task, or other skill must never invoke it on the user's behalf. An idea mentioned in conversation is not a spec request.
disable-model-invocation: true
user-invocable: false
---

# Nestor Spec

Turn an idea into work that can be executed. Two movements: an interview that extracts the
specification the user already holds implicitly, then a compilation that turns it into a
tree of Nestor tasks.

This skill writes no code and touches no file. Its only output is items in Nestor, and
that is the point: a specification left as a document is read once, while the same content
split into tasks gets picked up, tracked and closed. Everything below exists so that
whoever opens one of those tasks later can carry it out without coming back to ask a
question.

Conduct the whole session in the language the user writes in. The specification and the
task bodies are written in that same language.

## Identify the plugin version

Pass `{ "version_hash": "d6253857072898f9" }` on every Nestor MCP call.

## Arguments

```
/nestor-beta:spec <idea…> [project:<name-or-id>]
```

Everything that is not the `project:` argument is the idea, however loosely phrased.
Preserve everything after the first colon in `project:`, including spaces in a project name.

An empty argument string is not an error. There is nothing to guess wrong here: the idea is
whatever the user is about to say. Ask for it in one line, then start from the answer.

The project is resolved late, at Stage 4, not now. A session that ends early then costs
nothing, and the user is not interrupted before the work has taken shape.

## Stage 1 — The interview

Ask one question at a time. Only one, and it must be a real one — "and also, by the way"
smuggles a second question into the first.

Two reasons this matters more than it looks. The answer to question *n* determines what
question *n+1* should be; asked together, the second question is aimed at a target that
has not appeared yet. And a person answering six questions at once answers all six
briefly, which is the opposite of what a specification needs.

**Open where the risk is.** The first question shows you read the idea: aim it at the
largest unknown, not at a restatement of what the user just wrote.

**Follow the answers, not a checklist.** Over the session the ground to cover is the
problem and who has it, the expected behaviour and its edge cases, the data — shape,
source, lifetime —, the architecture and the constraints already in place, what happens
when things fail, and how anyone would know it works. That is the territory, not an order
of march. Let each answer point at the next question.

**Never ask what the repository can answer.** When the session runs inside a codebase,
read it. Asking the user which test runner the project uses spends their attention on
something a single command settles.

**Prefer a decision to a blank question.** "What date format do you want?" makes the user
design; "I'll store instants in UTC, ISO 8601 — any constraint against it?" makes them
confirm in one word. Both are questions; the second respects the fact that their attention,
not your tokens, is the scarce resource. Keep the open form for what genuinely belongs to
them: money, risk, priority, taste.

**Recognise the natural end.** The interview is over when no blocking user decision remains
and the requirements can be stated in verifiable terms. Verified facts and the documented
technical choices allowed in Stage 2 do not need separate confirmation. Say so and offer to
compile — do not compile unannounced. The user often has one last thing in mind, and it is
cheaper to hear it now than to rewrite a tree.

## Stage 2 — Compile the specification

Write the specification and show it in the conversation. It must let a developer start
immediately, so it covers:

- **Requirements** — what the thing does, in verifiable statements. "Fast" is not a
  requirement; "answers under 200 ms for 95% of reads" is.
- **Architecture** — the components, their responsibilities, and how they talk. Include the
  choices that were made *and rejected*, with the reason: that is what stops a future
  reader from re-opening a settled question.
- **Data handling** — the shapes, where they live, how they migrate, what is kept and for
  how long.
- **Error handling** — what fails, what the system does about it, and what the user sees.
- **Testing plan** — how each requirement above is checked, and at which level.

**A gap is a question only when the gap is the user's to fill.** The three cases the
interview already draws still hold here: what the repository can answer, you read; a
technical choice the user has shown no interest in owning, you make and you write down in
the text, where it can be contradicted; what turns on money, risk, priority or taste, you go
back and ask. Only that third kind is worth an interruption — and it is also the one where
settling it silently costs the most, because an assumption written into a specification
stops looking like an assumption within a day, once work has been built on top of it.

## Stage 3 — Break the specification into a task tree

Do this thinking before writing anything into Nestor.

Draft the step-by-step blueprint. Break it into iterative chunks that build on one another.
Then look at those chunks and break them again. Review the result and check the steps are
small enough to be implemented safely, large enough to move the project forward. Iterate
until the sizing is right for *this* project — a migration and a prototype do not have the
same grain.

### Right-sized

A step is right-sized when an executor can finish it and verify it without waiting for a
later step to give it a purpose.

- If a task delivers two things that could each stand on their own, it is two tasks. Count
  deliverables, not sentences: several acceptance criteria describing one deliverable —
  a route answering 200 here and 503 there — are one task.
- If a task can only be verified after the next one lands, it is half a task — merge it.
- Each task builds on the ones before it and **ends by wiring things together**. Nothing
  written in a task may be left unreachable from the rest of the system: orphaned code is
  the failure mode this whole decomposition exists to prevent.

### The shape of the tree

The tree is fractal. Two kinds of task, and a parent may hold either kind.

**A pure orchestrator task** implements nothing. It exists so that progress is visible at
its level. Its body says what the group delivers, then lists its children in order with the
milestone each one closes. State plainly in the body that this task is complete only when
all of its children are — an orchestrator that gets closed on its own hides unfinished work.

The root is always a pure orchestrator, and it carries the full specification from Stage 2
in its body. That is what makes the tree readable a month later.

Give a section its own intermediate orchestrator when it holds enough actionable steps to
be followed on its own — roughly three or more. **Never create an orchestrator with a
single child**: a level that organises one thing organises nothing.

That rule holds at the root too. When the whole idea turns out to fit in one actionable
task, write that single task and nothing above it. The specification then lives in its
body, alongside the steps. A tree is a way to make progress visible, not a formality to
satisfy.

**An actionable task** is the unit someone picks up and finishes. Its body is read by an
executor who did not attend the interview and may have no way to ask a question — so it
must stand alone:

- The context it needs: what already exists at that point, what this step adds, and why.
- The steps, in order.
- No open decision. Not one. "Choose between X and Y" hands the user's own call to whoever
  happens to run the task, and that choice then arrives as a surprise inside the result.
- A runnable verification per section, and an explicit "done when" for the task.
- The wiring: how what it produces connects to what is already there.

Anchors — file paths, symbols — are worth including when they exist today. They turn the
executor's first move into a read rather than a search.

A parent and its children are one coherent deliverable, not unrelated work filed under a
common heading. That is what makes closing the parent mean something.

## Stage 4 — Confirm, then write it into Nestor

**Show the tree before writing it.** Indented titles, one line each, with the kind of every
node — orchestrator or actionable. Then ask for confirmation. Creating the tree is N
writes; undoing it is N trash confirmations, each of which the user has to give by hand.

### Resolve the project

Only once the user has confirmed the tree.

**Reuse the project already provided.** Use the `project:` argument or the project the user
gave during the interview. Ask which project the work belongs to only when it is missing,
in one line. If the user explicitly says the work belongs to no project, use
`{ "mode": "global" }`.

Reuse an id already resolved for the chosen project. Otherwise resolve the supplied value
with `get_project` before creating any task:

- For an explicit name, pass `name`; for an explicit id or prefix, pass `projectId`.
  Use the returned id when that lookup resolves unambiguously.
- When `project:<name-or-id>` leaves the interpretation open, make two separate reads,
  one with `name` and one with `projectId`. An exact name can also be another project's
  valid id prefix; the first successful lookup does not settle that ambiguity.
- Proceed with the returned id when both reads identify the same project, or when exactly
  one resolves and the other returns `NOT_FOUND` or rejects the reference format.
- If the reads identify different projects, a lookup is ambiguous, or neither resolves,
  ask one question to identify the intended project before any write. Other errors leave
  resolution incomplete: report them and stop rather than treating them as no match.

Resolve silently when the result is unambiguous. Call `list_projects` only when the user
asks what projects exist; never list them to accompany the project question.

### Create the tasks

Every call carries `version_hash` and the resolved `scope`.

1. Create the root with `create_item`, `type: "task"`, no `parentTaskId`, and the full
   specification as `body`.
2. Create each remaining task with the id its parent returned. A child needs its parent's
   id, so the tree is written top-down.
3. Use `backlog: true` on every task. This is planned work, not work due today, and
   scheduling twenty tasks onto the current day buries the rest of the journal.

Titles are short and imperative, in the style of a commit subject.

**If a creation fails partway through, stop.** Report exactly which tasks exist, with their
slugs, and which one failed. Never restart the tree from the root: that duplicates
everything already written, and two parallel trees are far more expensive to untangle than
one half-written one.

A lost response is not a refusal. A timeout may well have created the task, so report that
node as unknown rather than failed, and check what exists before anyone resumes.

### Report

Give the root's identifier — its slug when the creation returned one, its id otherwise —
and the number of tasks created. Nothing more: the tree was shown before the write, so
repeating it spends the user's attention on something they just approved.

## What this skill never does

- It never asks two questions in one turn. That is the whole method, not a stylistic
  preference.
- It never presents an unverified fact as established or silently settles a decision that
  belongs to the user. Documented technical choices allowed in Stage 2 remain valid.
- It never writes into Nestor before the user has confirmed the tree.
- It never leaves an open decision in an actionable task.
- It never creates an orchestrator with a single child.
- It never writes code, edits a file, or creates a branch. It specifies; it does not
  implement.
