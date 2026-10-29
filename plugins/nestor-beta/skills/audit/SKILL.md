---
name: audit
description: Have an independent agent audit one Nestor Plan or Task, or one pull request given by its number, by default a subagent of the current client; only the word cli among the arguments runs a Codex or Claude CLI process instead, Codex sol6.1 at xhigh by default. The other arguments choose the agent, model and effort by their meaning. For a Plan or Task, it audits the stored specification against the repository until the item is delivered, then the delivered code against that specification; the report is logged in a Nestor note linked to the audited item. For a pull request number, it audits that pull request's changes against its title and description. Use when the user or an agent asks to audit an item reference or a pull request number; an agent invokes it on its own with the same arguments and ends with the report as the result. Do not use for a review that the agent makes itself.
argument-hint: "<plan-or-task-id-or-slug|pr-number> [cli] [codex|claude] [model] [effort]"
---

# Nestor Audit

Have one Plan or Task, or one pull request, audited by an independent agent: by default a
subagent of the current client, or, with the word `cli`, a Codex or Claude agent that runs
in its own process. The report on a Plan or Task is then logged in a Nestor note linked to
that item. The calling agent reads the audited work, pins the commits, writes the brief,
launches the audit, waits for its end and gives the report. This file only routes the
audit: each step lives in the reference files it names.

## Identify the plugin version

Pass `{ "version_hash": "24c8b125c28bbbc43" }` on every Nestor MCP call.

## 1. Invocation

- Claude Code: `/nestor-beta:audit <ref|PR> [cli] [agent] [model] [effort]`.
- Codex: `$nestor-beta:audit <ref|PR> [cli] [agent] [model] [effort]`.
- Cursor: select the skill, then supply the arguments.

An agent can also invoke the skill on its own, with the same arguments, when an audit is
asked of it: by its user in plain words, by its instructions, or by the agent that started
it, as for a subagent. It then follows these steps itself and ends with the report, which is
the result of the audit for whoever asked.

Read the arguments after the skill name, including a final `ARGUMENTS: …` line when the
client supplies one; an invocation without arguments takes them from the request that asked
for the audit.

## 2. Route the audit

The first word is either a Nestor reference — an id, an id prefix or an exact slug — or a
pull request number: digits only, with or without a leading `#`. Without a reference or a
number, ask for one in one line and stop.

The word `cli` or `CLI`, anywhere among the other words, is the only one that runs the audit
through a CLI; without it, a subagent of the current client audits. The mode file reads
every other word: an agent, a model or an effort.

Read the files in this order, and neither the other mode file nor the other branch file:

1. The mode file, [references/subagent.md](references/subagent.md), or
   [references/cli.md](references/cli.md) with the word `cli`, to validate the words before
   any read or write.
2. The branch file, [references/nestor-item.md](references/nestor-item.md) for a reference,
   or [references/pull-request.md](references/pull-request.md) for a number, to read the
   audited work, pin its commits and write its part of the brief.
3. [references/brief.md](references/brief.md), to complete the brief.
4. The mode file again, to launch the audit and wait for the report.
5. The branch file again, to end the audit: the linked note and the citation for a Plan or
   Task, the link to the pull request for a number.
