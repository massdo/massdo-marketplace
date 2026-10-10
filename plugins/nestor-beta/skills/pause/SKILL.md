---
name: pause
description: Save a project's work context and summaries in a Nestor handoff note for a later conversation. Use only when the user explicitly invokes pause; an agent, subagent, plan, memory, Nestor task or other skill must never invoke it on their behalf.
argument-hint: "[project]"
disable-model-invocation: true
---

# Nestor Pause

Capture the context of interrupted work in one project. The agent writes the summaries;
Nestor stores them. The handoff describes the state at capture time and lets `resume`
restore it without reading the linked tasks or notes.

The `nestor` skill governs shared MCP procedures, conditional reads and item citations.
This workflow creates one note; it changes no existing task or note and keeps no local
handoff storage.

## Identify the plugin version

Pass `{ "version_hash": "2a2cc476ca4c165c2" }` on every Nestor MCP call.

## Invocation and project

- Claude Code: `/nestor-beta:pause [project]`.
- Codex: `$nestor-beta:pause [project]`.
- Cursor: select the skill, then supply the project name.

Run only after a direct invocation by the user. Read the arguments after the skill name,
including a final `ARGUMENTS: …` line when the client supplies one. The whole argument
string is one project name: preserve internal spaces. Blank arguments mean no project
was supplied.

An explicit project takes precedence over the workspace; do not read Git to replace it.
Otherwise use the same resolution as `next-tasks`, without invoking that skill:

1. Find the workspace's Git root; a subdirectory or linked worktree must resolve as its
   root does.
2. Read `origin` and take the last URL segment without `.git`, recognizing HTTPS, SSH
   and SCP forms. With no `origin`, take the root directory's name.
3. If no reliable name results, ask for a project and stop before any mutation.
4. Read the exact name with `get_project`. Only a not-found result permits
   `search_project` with that name as `query`; a transport or authentication error is
   reported as a failure. A single result in total may be retained; several results or
   an incomplete page require clarification. Announce a retained name that differs.
5. Stop on an archived project: it cannot accept the handoff. Never create a project
   automatically or fall back to all projects.

Use `{ "mode": "project", "projectId": "<resolved id>" }` for every scoped call below.
