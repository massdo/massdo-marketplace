---
name: resume
description: Restore a project's saved Nestor handoff and archive that note, without starting work. Use only when the user explicitly invokes resume; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Resume

Restore the context and proposed next actions saved by `pause`. Read only the selected
handoff note's body, prepare the response, then archive that note automatically.
Do not start work or invoke another skill.

The `nestor` skill governs shared MCP procedures, conditional reads, optimistic
mutations and item citations. Its journal MCP server is provided by the nestor plugin.

## Identify the plugin version

Pass `{ "version_hash": "2a2cc476ca4c165c2" }` on every Nestor MCP call.

## Invocation and project

- Claude Code: `/nestor-beta:resume [project]`.
- Codex: `$nestor-beta:resume [project]`.
- Cursor: select the skill, then supply the project name.

Run only after a direct user invocation. Read arguments after the skill name, including
a final `ARGUMENTS: …` line when supplied by the client. The whole argument string is
one project name: preserve internal spaces. Blank arguments mean no explicit project.

An explicit project takes precedence over the workspace; do not read Git to replace it.
Otherwise use the resolution of `next-tasks`, without invoking it:

1. Find the workspace's Git root, including from a subdirectory or linked worktree.
2. Take the last segment of `origin` without `.git`, recognizing HTTPS, SSH and SCP
   forms. With no `origin`, take the root directory's name.
3. If no reliable name results, ask for the project and stop before any mutation.
4. Read the exact name with `get_project`. Only a not-found result permits
   `search_project` with that name as `query`. Report transport or authentication
   failures instead of treating them as an absent project. Retain a single result in
   total; several results or an incomplete page require clarification. Announce a
   retained name that differs.
5. Stop on an archived project: it cannot accept the required archive mutation. Never
   create a project automatically or fall back to all projects.

Use `{ "mode": "project", "projectId": "<resolved id>" }` for every scoped call below.

## Reading budget

Discovery reads only handoff metadata. In the normal path, one `get_item` reads the
selected handoff; a conditional unchanged response reuses its held content.
Never read a linked task or note, resolve its slug, verify its current status, compare
its versions or consult its history. Do not inventory tasks or search their contents.
Do not use snapshots or `list_events` to enrich the response. These limits also apply
to error and conflict handling: an inaccessible linked slug still has its saved summary.
