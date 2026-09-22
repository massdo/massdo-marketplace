---
name: nestor
description: Use the Nestor MCP server as the canonical source whenever the user asks to consult or change tasks, todos, action items, backlog, journal entries, notes, memos, reminders, history, journal projects, tags, priorities, due dates, pending work, or next actions. Trigger even when the user does not mention Nestor or MCP, including equivalent requests in any language such as asking what to do next, recording something, adding or completing a task, logging progress, checking project status, or finding a past note. Use the activity skill instead for starting, switching, stopping, repairing, or reporting activity time. Do not trigger for generic software logs or unrelated project work unless the user asks to store or retrieve that information in the journal.
metadata:
  pluginVersion: "0.7.3"
---

# Nestor Journal

## Identify the plugin version

This plugin version is 0.7.3, hashed as `ad3a12df4031d2d7`.

Pass `version_hash` on every call to a Nestor MCP tool, like `{ "version_hash": "ad3a12df4031d2d7", ... }`. The server compares this hash to the published release. It cannot be guessed or incremented, so never send another value than the one written here.

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

- Use `get_item` when id or slug is known, whatever the read is for. For a single item, pass the received reference as a string in `ref`, together with `scope` and `version_hash`; the response holds `item` and `etag`. Never send `id`, `slug` or `refs` as input keys to this tool. A single field, a status check, and a full read all take the same tool.
- When several known items need a full read, pass an array of 1 to 5 references in `ref` in one `get_item` call, together with `scope` and `version_hash`. An array always returns `results`, even with one reference. Match `results[i]` with the input `ref[i]` and check the echoed `ref`. Preserve repeated entries. An entry with `error` concerns that position only. Leave out any item whose content and matched pair are already held.
- Use `search_items` only when the user describes content and no id or slug is known.
- Use `list_items` for views and unfiltered lists.
- Treat `recent` as the default view. Query backlog, completed, cancelled, or trashed work only when requested.
- Use `get_project` to resolve a project the user names: it reads by exact `name` as well as by id. Keep `search_project` for browsing every project, called without a `query`, or for proposing candidates when the given name matches none, called with that name as `query`. Never guess a project identifier.
- Report incomplete results whenever a response has `hasMore: true`.

## antipattern

An `antipattern` is an action the agent must avoid at all costs. The first three entries govern reads; the others protect optimistic mutations:

- `search_for_known_identity`: never call `search_items` or `list_items` to reach an item whose id or slug is already known, not even to read a single field or to avoid a long body. `get_item` is the only deterministic access to a known item. Search matches the title and body, which the user rewrites at any time, so a renamed item stops matching a query that worked yesterday. The entries below forbid several `get_item` calls; none of them makes a search the substitute.
- `search_project_for_named_project`: never call `search_project` to resolve a project the user names. `get_project` reads a project by exact `name`, so a named project is a deterministic read, exactly like an item whose slug is known. `search_project` matches names loosely and returns candidates, so a close name comes back for a project the user never meant, and it pages once the journal holds more projects than a page. Call it only when the user wants to see all the projects, without a `query`, or when the exact read finds nothing and the candidates have to be proposed, with the failed name as `query`. A fuzzy result never authorizes a write on its own: the user confirms the project first.
- `get_item_burst`: never issue avoidable separate `get_item` calls for known references that one call with an array in `ref` can read. Use at most 5 references per call. Smaller groups are allowed for known large content, client output limits, different scopes, or reads that depend on earlier results.
- `preventive_get_item_before_update`: never call `get_item` immediately before `update_item` when a matched `version` and `etag` pair is already held. Send that pair directly. A `create_item` or `update_item` response already holds that pair, as does a conflict's `details.current`, so a mutation right after a creation, another mutation, or a conflict with that field needs no `get_item`.
- `post_success_get_item`: never call `get_item` after a successful `update_item` only to verify the change. Trust the confirmed mutation result. A transport HTTP 502 is not a confirmed success; report the uncertain outcome instead of using a verification read to infer it.
- `stale_version_etag_pair`: never reuse the pair you already sent to a mutation. After a conflict, discard the rejected pair; the next held pair is `item.version` and `etag` from `details.current` when that field is present, or from one fallback `get_item` when it is not. A successful `create_item` or `update_item` returns a fresh pair; use that one for the next change. A pair belongs to the item, not to the operation that returned it: the pair handed back by a status `patch` is the one the next `add_link`, `add_tags`, `remove_tags`, `append_body` or `move` on that same item must send. Treating a different operation as a fresh start is how a held pair gets dropped and a `get_item` gets paid for nothing. If the server rejects a missing, invalid, or stale precondition, examine the current state, adapt the change, and retry the same operation once with the new pair. Never replay the rejected patch unchanged.
- `mixed_version_etag_reads`: never combine `version` from one response with `etag` from another. Use both values from the same response, whether it comes from `get_item`, `create_item`, `update_item`, or a conflict's `details.current`. After a read with an array in `ref`, take both values from the same `results` entry. After mutating an item, reuse the mutation's returned pair. Another previously read entry for that item cannot replace it.

## Update items

- Pass `expectedVersion` and `expectedEtag` directly when a matched pair from an earlier `get_item`, `create_item`, `update_item`, or a conflict's `details.current` is still held. Never refresh a held pair immediately before the mutation.
- When no valid pair is held, call `update_item` without a precondition.
- If the server rejects the mutation for a missing, invalid, or stale precondition, examine the current item, adapt the change to that state, and retry the same operation once with that item's pair. Never replay the rejected patch unchanged onto the new pair.
- Take that current item from `details.current` when the conflict includes it. That object has the same shape as a `get_item` response: `item.version` and `etag` come from there, so no extra `get_item` is needed. Call `get_item` once only when the rejection has no `details.current`, including a missing precondition and older servers that still return an empty conflict.
- Never combine values from different responses. After a conflict, discard the pair that was just rejected. After a successful mutation, use the pair that response returns for the next change on that item, whatever operation that change performs.
- Repeat a rejected mutation only once. Report the conflict when the second attempt also fails.
- Use `append_body` to add text to a body. Never read an item only to resend an unchanged body.
- Use `update_item` only for requested fields and operations.
- Treat `need_review` as active work. Use it for review requests and return it to `in_progress` when changes are required.

## Use other journal tools

- Use `get_item_version` for a freshness check only. It never prepares a mutation, because it returns no ETag.
- Use `item_history`, `list_events`, or `project_history` for history.
- Use `list_tags` and `manage_tag` for tags.
- Use `get_project`, `search_project`, `manage_project`, and `project_history` for projects.
- Use `configure_journal` only for journal configuration. Read the current configuration before changing it.
- Treat `@@tags` as a tag consultation and `@@config` as a configuration request. Do not create items from them.

## Protect mutations

- Never turn a read request into a mutation.
- Mutate only the requested records and fields.
- Obtain explicit user confirmation before trashing an item or confirming deletion of a tag or project.
- After each mutation, report the confirmed result, affected identifier, and any warning.

## Cite items

- Name every item a response cites as `slug (description)`, for example `green_earwig (commande manuelle de signalement des appels MCP)`.
- Apply that form to each item of a list, a search result, or a mutation report.
- Keep the description to a few words naming the item's business subject, in the language of the conversation. Never copy the whole title.
- Write the description from data already held, and leave it out when none is. Never call a tool only to write it.
- The form only names the item. It never replaces the details the user asked for, such as its status or body.
