---
name: nestor-beta
description: Extension of the nestor skill. Use whenever code is written from Nestor tasks, and whenever a branch, a commit or a pull request is created or updated for such code, to trace those tasks in the pull request footer and keep their ids and slugs out of branch names, commit subjects and pull request titles. Trigger even when the user mentions neither a footer nor traceability, in any language. Do not trigger for journal operations that involve no code change.
metadata:
  pluginVersion: "0.11.0"
---

# Nestor Beta

This skill extends the `nestor` skill, which governs every journal operation, with the
rules that link code to the Nestor tasks it implements.

## Identify the plugin version

Pass `{ "version_hash": "2a2cc476ca4c165c2" }` on every Nestor MCP call.

## Trace tasks in the pull request footer

A pull request whose changes implement Nestor tasks ends its description with one visible
line, the last of the description, with nothing after it — a signature or attribution line
goes above.

```
nestor tasks: brown_turtle, gray_xerinae, copper_manatee
```

- Write each task's slug exactly as Nestor returns it, never an id: an id comes back
  shortened to a length that varies from one response to the next, a slug does not.
- Separate them with a comma and a space, and write each slug once.
- List the tasks the changes actually contribute to, the subtasks concerned included. A
  task that is only mentioned as a dependency stays out.
- A partial contribution may be listed: the footer links a task to the code, it does
  not declare the task finished.

Keep the footer true as the pull request evolves: keep every slug already listed and add
the new ones, and adjust the title when the scope changes.

## Keep branches, commits and titles descriptive

A Nestor id or slug never goes in a branch name, a commit subject or a pull request title:
the footer is the only reference. Each of them describes the change instead — a branch such
as `feat/csv-export`, a commit subject that says what the commit changes — and the title is
in English. The repository's own conventions decide the rest.
