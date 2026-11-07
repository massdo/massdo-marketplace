---
name: implicit-state-machines
description: Find the implicit state machines in a codebase, meaning behavior that depends on states and transition rules the code never models explicitly. For each one, report its states, transitions, triggering events and guards with file and line, separate demonstrated defects from risks, and say whether an explicit form would pay off. Analysis only; it never edits code. Use when the user asks to find, map or audit implicit state machines, status fields, lifecycle flags or state transitions in their code, for a path given as argument or the whole repository. Do not use to fix one bug or to implement or refactor a state machine.
argument-hint: "[path, module or feature]"
---

# Implicit state machines

A state machine is implicit when the correctness of some behavior depends on the state an
entity is in and on which moves between states are allowed, while the code never declares
that rule: it lives in conditionals, flags and writes. Find these machines, describe them,
check them, and say whether making them explicit is worth it.

## Scope

The arguments are the text written after the skill name; depending on the client, they may
arrive on a final `ARGUMENTS: …` line. When the user asks in their own words, read the scope
from their message. A scope is one or more paths, a module, a feature or an entity name.
Without one, analyze the repository in the working directory.

This is an analysis. Do not edit, create or delete project files, even to fix an obvious
defect, and do not run anything that writes: installs, migrations, builds, formatters or
scripts with side effects. Reading, searching and the version history are enough. The user
decides what to change.

On a large scope, read first where state lives: data models, schemas and migrations, stores
and reducers, request handlers, background jobs, webhooks and multi-step UI flows. Never
present a partial reading as complete; what was not read goes in the limits of the report.

## What counts as a candidate

Each of these signals is a lead, not a finding:

- a field whose value belongs to a closed set, such as an enum, a union of string literals,
  constants, or a `status`, `state`, `phase`, `step`, `stage` or `mode` field;
- several booleans, timestamps or nullable fields that describe one lifecycle, where not
  every combination is valid, such as `isLoading` with `error` and `data`, or `paidAt`
  with `cancelledAt`;
- a check of the current state before acting: a condition, an early return, or an error
  raised on the wrong state;
- an order between calls: `init` before `use`, `connect` before `send`, step two only after
  step one, a retry loop, a timeout or an expiry;
- a lifecycle stored outside memory, such as a database row, a file, a cache key, a URL, a
  queue message or browser storage, or the same lifecycle held in two layers, such as
  client and server, or two records;
- a comment or a name that describes a lifecycle in prose, such as "once validated".

Keep a candidate only when all three hold:

1. the entity has at least two states whose allowed next moves differ;
2. no single declaration of the states and allowed moves governs every write; the rule
   lives in conditionals, flags and assignments, even when they sit in one function;
3. a wrong move would change observable behavior or stored data.

A rule spread across several functions or files, duplicated, or derived from a combination
of fields is not required, but it raises the maintenance cost when you rank the machine.

Set aside a toggle that gates nothing, generated or vendored code, and a machine that is
already explicit, such as a closed state type with one transition function or table that
every write goes through, or a state machine library. An explicit machine becomes a
candidate again when some code writes its state directly and bypasses the transitions.

Finding no implicit state machine is a valid result. Do not stretch a weak candidate to
have something to report.

## Method

1. Find where each candidate's state is stored and how it is typed.
2. Find every write to that state and every read that gates behavior. Search by field name
   and by literal values, since raw queries, serializers, dynamic keys and string literals
   escape a search by type. Include tests: they show the intended transitions, not proof
   that the code respects them.
3. Reconstruct the machine:
   - states, including implicit ones: the initial value or absent value, an intermediate
     state between two writes, and the terminal states. An intermediate state counts only
     when something can observe it: a read, a suspension such as an await or a callback,
     an external effect, or a stored record. Writes with none of these between them form
     one transition;
   - events: what triggers each write, such as a user action, a request, a job, a
     webhook, a timer or an error;
   - transitions, as origin, target and event;
   - guards: the conditions checked before each write. Mark a transition as checked when
     the code verifies its origin state, and as unchecked otherwise.
4. Infer the intended rule from the strongest evidence in the project: documentation,
   tests, error messages, UI flows, then names. When the intent stays unclear, say so
   instead of choosing one.
5. Look for defects:
   - a write that sets a state from any origin, while other code requires a given origin;
   - a reachable state that no code handles, or a non-terminal state with no way out;
   - a combination of fields that has no meaning, that the code can produce, and that a
     read, an external effect or a stored record can observe;
   - a terminal state that some path can leave;
   - two writers, such as two requests, a job and a request, or a redelivered webhook,
     that read then write the state when nothing serializes them: a lock, a transaction
     at the right isolation level, a conditional update, a unique constraint, an
     idempotency key or a single consumer;
   - two copies of the state that can diverge with nothing to reconcile them.
6. Classify each defect:
   - demonstrated: you can name the path from an entry point to the line that produces
     the invalid state or transition, under conditions that normal use of the application
     produces. Cite `file:line` for each step;
   - risk: the path depends on a condition the code does not establish, such as a timing,
     an input that no caller sends, or a misuse. Keep it only when that condition is
     plausible in normal use, and say what would confirm or rule it out. Do not build a
     finding on an unfavorable scenario that nothing in the code supports.
7. Decide whether an explicit form pays off, given the number of states and writers, the
   defects found, whether the state is stored, and how often this code changes. From the
   lightest form to the heaviest:
   - keep it as is, often the right answer for a few states with one writer;
   - a closed state type, such as an enum or a discriminated union, that replaces
     conflicting flags and makes invalid combinations impossible to represent;
   - one transition function or table that every write goes through and that rejects
     unknown moves;
   - a conditional write or a constraint where the state is stored, such as an update
     that matches the expected origin state, when concurrent writers exist;
   - a state machine library, only for many states, nested or parallel states, or timers,
     and only if the project accepts that dependency.

   Recommend one form in the project's own idioms and say why. A short sketch of the
   states and transitions is enough; do not write the implementation.

Cite only the files and lines you read during this analysis.

## Ranking

Rank the machines by the impact of their worst defect, then by their maintenance cost:

1. critical: a demonstrated defect that corrupts or loses stored data, performs an
   irreversible action twice or wrongly, such as a payment, a message or a deletion, or
   leaves a user or a record stuck with no way out;
2. high: a demonstrated defect with wrong but recoverable behavior, such as a wrong
   screen, a wrong message or a needed retry;
3. medium: no demonstrated defect, but unchecked transitions or rules duplicated across
   writers make the next change likely to break the machine;
4. low: a small, coherent machine, worth knowing about and not worth changing.

A risk ranks one level below the same impact demonstrated.

## Report

Write the report in the language the user writes in. Keep code identifiers, file paths and
technical terms in their original form.

Start with one line: the scope analyzed, the number of machines found, and the number of
demonstrated defects. Then give each machine, most important first:

- **name and level**: a short name for the machine and its ranking level;
- **where**: the fields that hold the state and the main functions that write it, with
  `file:line`;
- **states**: the list, with the initial and terminal states marked;
- **transitions**: one line each, with origin, target, event, guard, checked or unchecked,
  and `file:line`;
- **defects**: each one labeled demonstrated or risk, with its path and `file:line`; for a
  risk, what would confirm or rule it out;
- **explicit form**: the recommended form, or keep it as is, and why, in one or two
  sentences.

Then list the candidates set aside, one line each with the reason. End with the limits of
the analysis: what was not read, assumptions about intent, and what a static reading cannot
settle, such as dynamic dispatch, runtime configuration, database triggers, external
services or other repositories.

When no machine meets the criteria, say so, then give the candidates set aside and the
limits.
