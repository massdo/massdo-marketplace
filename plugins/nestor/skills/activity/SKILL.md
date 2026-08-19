---
name: activity
description: Track and report time spent on named activities in Nestor. Use when the user starts, switches, or stops an activity timer; asks for daily, weekly, or monthly activity totals; or wants to rename, merge, adjust, or delete activity data. Do not use for task status changes or general questions about physical activities.
---

# Nestor Activity

Use the Nestor MCP server to track time by activity. Never read or modify the journal
database, its files, or an export.

## Identify the plugin version

This skill ships with Nestor 0.3.0, hashed as `f918b2acb9fb1103`.

Pass `version_hash` on every tool call, for example
`{ "version_hash": "f918b2acb9fb1103", ... }`. Never send a different value.

- Relay a plugin update warning once in the conversation.
- If the server rejects the hash as unknown, say that the plugin must be updated.
- Never block the requested activity operation because of an update warning.

## Choose the operation

Activities are independent from journal tasks and projects. Never pass a journal scope,
task id, or project id to an activity tool.

- Start or switch an activity with `track_activity` action `start`.
- Stop the current activity with action `stop`.
- Read current activity, totals, buckets, and capped slots with `activity_report`.
- Rename, merge, adjust, or delete only when the user requests that mutation.

When `/nestor:activity` has no argument, call `activity_report` without a window. This
returns today's totals and the current activity.

## Start and switch

Call `start` with the activity name. A successful start closes the previous open slot and
opens the requested activity. Do not call `stop` before a switch.

An ambiguous result starts nothing and closes nothing. Show the candidate names and ids,
then ask the user to choose:

- A confirmed candidate starts with its `activityId`.
- A clearly requested new activity starts with the original name and `createNew: true`.

Never choose a candidate or force a new activity without the user's decision.

After a successful start or stop, report the activity and any closed duration. Mention
`capped: true` because the user may need to repair that slot.

## Report activity time

Use `activity_report` for every time summary. Without `from` and `to`, the report covers
local midnight through now. Without `groupBy`, it returns totals without buckets.

- Use `{ "date": "YYYY-MM-DD", "isAllDay": true }` for a local calendar date.
- Use `{ "instant": "...Z" }` or an explicit UTC offset for an exact instant.
- Treat `to` as an exclusive boundary.
- Use `day`, `week`, or `month` buckets only when the request needs that grouping.
- Filter by `activityId` only when the id is known.

Do not calculate local midnight or a UTC offset yourself. The report returns its effective
window and journal time zone. It is read-only: a capped open slot is projected, not closed.

Summarize only returned data. Include the current activity when present. Identify capped
slot ids so the user can repair them.

## Repair activity data

Rename and merge require current activity ids and versions. Reuse them only from a recent
`track_activity` or `activity_report` response. If the required activity is not observable,
ask for its id instead of starting it or guessing.

Merge keeps the target and removes the source after moving every source slot. Restate the
direction before the call when the user's wording does not clearly identify the target.

Adjust and delete require an exact slot id from a previous response or from the user.
Never infer a slot id from its position. For an adjusted timestamp, require an absolute
epoch value or enough offset information to derive one without guessing.

An optimistic conflict invalidates the versions held for rename or merge. Read fresh data
when possible. Retry only when the same requested activities remain unambiguous.

## Report the result

Report only MCP-confirmed changes. Include affected activity or slot ids when returned.
For an error, give its stable code and the action the user can take next.
