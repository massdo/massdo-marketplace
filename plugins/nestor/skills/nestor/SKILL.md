---
name: nestor
pluginVersion: 0.5.0
antipattern:
  - search_for_known_identity
  - list_projects_for_named_project
  - preventive_get_item_before_update
  - post_success_get_item
  - stale_version_etag_pair
  - mixed_version_etag_reads
description: Use the Nestor MCP server as the canonical source whenever the user asks to consult or change tasks, todos, action items, backlog, journal entries, notes, memos, reminders, history, journal projects, tags, priorities, due dates, pending work, or next actions. Trigger even when the user does not mention Nestor or MCP, including equivalent requests in any language such as asking what to do next, recording something, adding or completing a task, logging progress, checking project status, or finding a past note. Use the activity skill instead for starting, switching, stopping, repairing, or reporting activity time. Do not trigger for generic software logs or unrelated project work unless the user asks to store or retrieve that information in the journal.
---

# Nestor Journal

## Identify the plugin version

This plugin version is 0.5.0, hashed as `cce406ae1ed0ef21`.

Pass `version_hash` on every call to a Nestor MCP tool, like `{ "version_hash": "cce406ae1ed0ef21", ... }`. The server compares this hash to the published release. It cannot be guessed or incremented, so never send another value than the one written here.

- After every tool response, read `structuredContent.pluginUpdate` when present.
- If `pluginUpdate.status` is `update_available`, say exactly `Une mise à jour est disponible.`
- Do not relay `publishedVersion`, `action`, platform, installation, or automatic-update text.
- If the server rejects `version_hash` as unknown, say the plugin is too old and must be updated.

Never block the requested journal operation. Never write on disk. Never invent a client identifier.

`/nestor:check-for-updates` always reports the probe result, including `unknown`.

## Use the MCP as the source of truth

- Use the `nestor` MCP server.
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
- `create_item` returns the new item's `item.version` and `etag`. Reuse that pair directly for the next mutation, exactly like the pair a mutation returns. A creation never needs a following `get_item`.

## Find items and projects

- Use `get_item` when id or slug is known, whatever the read is for. Pass the received reference in `ref`, together with `scope` and `version_hash`. Never send `id` or `slug` as input keys to this tool. A single field, a status check, and a full read all take the same tool.
- Use `search_items` only when the user describes content and no id or slug is known.
- Use `list_items` for views and unfiltered lists.
- Treat `recent` as the default view. Query backlog, completed, cancelled, or trashed work only when requested.
- Use `get_project` to resolve a project the user names: it reads by exact `name` as well as by id. Keep `list_projects` for browsing every project, or for proposing candidates when the given name matches none. Never guess a project identifier.
- Report incomplete results whenever a response has `hasMore: true`.

## antipattern

An `antipattern` is an action the agent must avoid at all costs. The first two entries protect deterministic reads; the others protect optimistic mutations:

- `search_for_known_identity`: never call `search_items` or `list_items` to reach an item whose id or slug is already known, not even to read a single field or to avoid a long body. `get_item` is the only deterministic access to a known item. Search matches the title and body, which the user rewrites at any time, so a renamed item stops matching a query that worked yesterday. The entries below forbid several `get_item` calls; none of them makes a search the substitute.
- `list_projects_for_named_project`: never call `list_projects` to resolve a project the user names. `get_project` reads a project by exact `name`, so a named project is a deterministic read, exactly like an item whose slug is known. `list_projects` returns every project with its context to keep a single one, and pages once the journal holds more projects than a page. Call it only when the user wants to see all the projects, or when the name matches none and the candidates have to be proposed.
- `preventive_get_item_before_update`: never call `get_item` immediately before `update_item` when a matched `version` and `etag` pair is already held. Send that pair directly. A `create_item` or `update_item` response already holds that pair, so a mutation right after a creation or another mutation needs no `get_item`.
- `post_success_get_item`: never call `get_item` after a successful `update_item` only to verify the change. Trust the confirmed mutation result. A transport HTTP 502 is not a confirmed success; report the uncertain outcome instead of using a verification read to infer it.
- `stale_version_etag_pair`: never reuse the pair you already sent to a mutation, and never reuse any pair after a conflict. A successful `create_item` or `update_item` returns a fresh pair; use that one for the next change. A pair belongs to the item, not to the operation that returned it: the pair handed back by a status `patch` is the one the next `add_link`, `add_tags`, `remove_tags`, `append_body` or `move` on that same item must send. Treating a different operation as a fresh start is how a held pair gets dropped and a `get_item` gets paid for nothing. If the server rejects a missing, invalid, or stale precondition, call `get_item` once and retry the same operation once.
- `mixed_version_etag_reads`: never combine `version` from one response with `etag` from another. Use both values from the same response, whether it comes from `get_item`, `create_item`, or `update_item`.

## Update items

- Pass `expectedVersion` and `expectedEtag` directly when a matched pair from an earlier `get_item`, `create_item`, or `update_item` is still held. Never refresh a held pair immediately before the mutation.
- When no valid pair is held, call `update_item` without a precondition.
- If the server rejects the mutation for a missing, invalid, or stale precondition, call `get_item` once, then repeat the same operation with `item.version` and `etag` from that response.
- Never combine values from different responses. After a conflict, discard the pair and read again. After a successful mutation, use the pair that response returns for the next change on that item, whatever operation that change performs.
- Repeat a rejected mutation only once. Report the conflict when the second attempt also fails.
- Use `append_body` to add text to a body. Never read an item only to resend an unchanged body.
- Use `update_item` only for requested fields and operations.
- Treat `need_review` as active work. Use it for review requests and return it to `in_progress` when changes are required.

## Use other journal tools

- Use `get_item_version` for a freshness check only. It never prepares a mutation, because it returns no ETag.
- Use `item_history`, `list_events`, or `project_history` for history.
- Use `list_tags` and `manage_tag` for tags.
- Use `get_project`, `list_projects`, `manage_project`, and `project_history` for projects.
- Use `configure_journal` only for journal configuration. Read the current configuration before changing it.
- Treat `@@tags` as a tag consultation and `@@config` as a configuration request. Do not create items from them.

## Protect mutations

- Never turn a read request into a mutation.
- Mutate only the requested records and fields.
- Obtain explicit user confirmation before trashing an item or confirming deletion of a tag or project.
- After each mutation, report the confirmed result, affected identifier, and any warning.
