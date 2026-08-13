---
name: nestor-journal
description: Use the Nestor MCP server as the canonical source whenever the user asks to consult or change tasks, todos, action items, backlog, journal entries, notes, memos, reminders, tracking logs, history, journal projects, tags, priorities, due dates, pending work, or next actions. Trigger even when the user does not mention Nestor or MCP, including equivalent requests in any language such as asking what to do next, recording something, adding or completing a task, logging progress, checking project status, or finding a past note. Do not trigger for generic software logs or unrelated project work unless the user asks to store or retrieve that information in the journal.
---

# Nestor Journal

## Use the MCP as the source of truth

- Use the `nestor-journal-assistant` MCP server. Accept `nestor-task-assistant` as its legacy local name.
- Make at least one relevant MCP call before giving a substantive journal answer.
- Verify current data through the MCP instead of relying on conversation memory.
- Never bypass the MCP by reading or changing SQLite databases, journal files, exports, or repository data.
- Report MCP unavailability clearly. Never invent journal data or claim an unconfirmed mutation.

## Recognize journal intent

- Treat something to do later as a task.
- Treat a decision, idea, lesson, observation, or explicit request to record something as a note.
- Treat a completion, cancellation, start, or review request as a status change on an existing task.
- Read the journal for questions about pending work, progress, or previously recorded information.
- Preserve marker-prefixed text exactly. The default markers are `@@task`, `@@note`, `@@tags`, and `@@config`.
- Ignore passing mentions of tasks, notes, logs, or history during unrelated coding and debugging unless durable journal storage is intended.

## Execute the request

1. Classify the request as a read, search, creation, update, organization, history, or configuration operation.
2. Resolve missing project, item, or tag identifiers through MCP reads.
3. Pass an explicit scope to every scoped tool. Use global scope unless the user names a journal project.
4. Ask a focused question only when MCP results leave multiple plausible targets or required mutation details remain unknown.
5. Perform the requested operation and summarize only MCP-confirmed results.

## Create items

- Use `create_item` with a non-empty title for a task or a non-empty body for a note.
- Preserve the user's wording and any marker. Do not translate or polish journal text.
- Use `backlog: true` for unscheduled someday work. Do not combine it with a non-null `scheduledAt`.
- When the user gives no timing, accept the server's current default and report the resulting schedule.
- Prefer an all-day date unless the user gives a time.
- Add known tags during creation with `tagNames`.

## Find items and projects

- Use `search_items` when the user describes content.
- Use `list_items` for views and unfiltered lists.
- Treat `recent` as the default view. Query backlog, completed, cancelled, or trashed work only when requested.
- Use `get_project` or `list_projects` to resolve a project. Never guess a project identifier.
- Report incomplete results whenever a response has `hasMore: true`.

## Update items safely

- Use `get_item` to obtain the current state and a matched version-and-ETag pair.
- Before `update_item`, call `get_item` if no matched pair is held.
- If a pair is already held, call `get_item_version`. Reuse the pair when the version matches. Refresh it with `get_item` when the version differs.
- Pass the matched values as `expectedVersion` and `expectedEtag`. Never combine values from different reads.
- After a mutation or conflict, discard the pair. Acquire a new pair before another mutation.
- Use `update_item` only for requested fields and operations.
- Treat `need_review` as active work. Use it for review requests and return it to `in_progress` when changes are required.
- Follow the active tool schema and server instructions when they differ from this skill.

## Use other journal tools

- Use `get_item_version` only to validate a held version-and-ETag pair. It cannot establish a new pair because it returns no ETag.
- Use `item_history`, `list_events`, or `project_history` for history.
- Use `list_tags` and `manage_tag` for tags.
- Use `list_projects`, `get_project`, `manage_project`, and `project_history` for projects.
- Use `configure_journal` only for journal configuration. Read the current configuration before changing it.
- Treat `@@tags` as a tag consultation and `@@config` as a configuration request. Do not create items from them.

## Protect mutations

- Never turn a read request into a mutation.
- Mutate only the requested records and fields.
- Obtain explicit user confirmation before trashing an item or confirming deletion of a tag or project.
- After each mutation, report the confirmed result, affected identifier, and any warning.

