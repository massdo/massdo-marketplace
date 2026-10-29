# Audit through a subagent

Without the word `cli`, a subagent of the current client audits. The calling agent
launches it through the client's own subagent mechanism, with the whole brief as its
prompt, waits for it to end and takes its last message as the report. Nothing is written
to a file in this mode.

## Read the words

Read the other words by their meaning, in any order, case or abbreviation, to choose the
subagent's model and effort:

- Effort: `low`, `medium`, `high`, `xhigh` or `max`.
- Model: one that the client runs, named by its family, such as `opus` in Claude Code, or
  by a version only when the client's subagent mechanism takes that version as such.

A word that names the current client itself, such as `claude` in Claude Code, chooses
nothing more. Without a model or an effort, the subagent runs with none imposed. Pass the
chosen model and effort to the subagent as the client's mechanism takes them; a model or
effort that this mechanism cannot take as such, such as a version where it takes only a
family name, is a word that the client cannot run.

When a word means nothing here, or names what the client cannot run, such as `codex`, `sol`
or `astra` in Claude Code, `claude` or `opus` in Codex, or `ultra`, or when the words name
two models or two efforts, ask in one line for the intended choice with the accepted values
and stop there. Read and write nothing before a valid choice comes back.

## Launch the audit

Launch one subagent through the client's own mechanism, with the whole brief as its prompt.
The subagent inherits the calling agent's configuration, such as its MCP servers,
instructions and hooks, without any restriction of its tools: the brief's rules are what
keep it read-only and out of the journal.

Wait for the subagent to end; its last message is the report. On the user's invocation,
say meanwhile in one sentence that the audit is running, with the client and, when one was
chosen, the model. When an agent invoked the skill on its own, keep waiting for the
subagent within the same turn and write nothing before the report: whoever asked, such as
the agent that started a subagent, may receive only what the turn ends with.

On an error of the subagent or an empty last message, write no note: say that the audit
failed and give its cause in plain words.
