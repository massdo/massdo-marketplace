# Audit through a CLI

With the word `cli`, a Codex or Claude agent audits in its own process, outside this
conversation. The calling agent writes the brief to a file, launches the agent's command
and reads the report back from a file. The auditor only reads the repository and has no
access to the journal.

## Read the words

Read the other words by their meaning, in any order, case or abbreviation, to choose the
agent that audits, its model and its effort:

| Agent | Families | Latest model, for `best` or no version | Efforts |
| --- | --- | --- | --- |
| `codex`, the Codex CLI | `sol`, `astra` | `gpt-6.1-sol` (sol6.1), `gpt-6-astra` (astra 6) | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `claude`, Claude Code | `opus`, `fable`, `sonnet`, `haiku` | the family name, which Claude Code resolves | `low`, `medium`, `high`, `xhigh`, `max` |

A model family alone names its agent, and `codex` without a family runs sol. A version the
words name runs that model, such as `sol 6` for `gpt-6-sol` or `opus 5.5` for
`claude-opus-5-5`. Without an agent or a model, the audit runs sol6.1; without an effort, it
runs at `xhigh`.

| Words | Audit |
| --- | --- |
| `cli codex sol best max` | sol6.1 at max |
| `cli claude op best max` | the latest Opus at max |
| `cli codex astra` | astra 6 at xhigh |
| `cli claude fable best` | the latest Fable at xhigh |

When a word means nothing here, when the words name two agents, models or efforts, or a
model or effort that the agent does not offer, such as `claude sol` or `claude ultra`, or
when they name `claude` without a family, ask in one line for the intended choice with the
accepted values and stop there. Read and write nothing before a valid choice comes back.

Once the choice is valid, check that the agent's command, `codex` or `claude`, is on the
PATH. Without it, stop before any read or write and say that the audit requires that CLI,
installed and signed in.

## Write the brief

Create a new private temporary directory with `mktemp -d` and write the brief to `brief.md`
there.

## Launch the audit

Run the agent's command from the repository root, with the brief's directory as `<dir>` and
the effort read above as `<effort>`.

For Codex, `<model>` is the model read above, such as `gpt-6.1-sol` or `gpt-6-astra`,
`<repo-root>` is the repository root, and `<skills-off>` holds one
`{path="<file>",enabled=false}` entry, comma separated, for each file that
`find -L ~/.codex/skills ~/.agents/skills -name SKILL.md` returns:

```sh
codex exec --ignore-user-config -c 'skills.bundled.enabled=false' -c 'skills.config=[<skills-off>]' --model <model> --config 'model_reasoning_effort="<effort>"' --sandbox read-only --cd <repo-root> --output-last-message <dir>/report.md - < <dir>/brief.md > <dir>/audit.log 2>&1
```

`--ignore-user-config` keeps the user's memories, MCP servers, plugins and hooks out of the
audit: nothing from another session enters it, and the auditor cannot write to the journal.
Codex keeps its own sign-in. It still loads skills without that configuration, so the two
`skills` overrides turn off its bundled skills and each of the user's own; a whole skills
folder cannot be turned off at once. `--sandbox read-only` lets the auditor change nothing
and gives it no network, which is why the calling agent fetches and pins the commits
beforehand.

For Claude, `<model>` is the family name, which Claude Code resolves to its latest model, or
the full name of the version the user named:

```sh
claude -p --safe-mode --setting-sources "" --model <model> --effort <effort> --tools Bash --allowedTools "Bash(git ls-tree *)" --permission-mode dontAsk --no-session-persistence < <dir>/brief.md > <dir>/report.md 2> <dir>/audit.log
```

`--safe-mode` and the empty `--setting-sources` keep the user's CLAUDE.md files, memory,
settings, plugins, hooks and MCP servers out of the audit: nothing from another session
enters it, and the auditor cannot write to the journal. Claude Code keeps its own sign-in.
`--tools Bash` with `--permission-mode dontAsk` leaves the auditor only the commands that
change nothing: Git reads run, while file writes and network requests are refused without
waiting for an approval. `--allowedTools` adds `git ls-tree`, a read that Claude Code does
not count among them. `--no-session-persistence` keeps the audit out of the user's
sessions.

Wait for the process to end without reading `audit.log`; only `report.md` comes back into
the conversation, at the end. When the client cannot keep a command in the foreground until
the audit ends, run it in the background and resume when it ends. On the user's invocation,
say meanwhile in one sentence that the audit is running, with the agent and its model, the
cited item or the pull request, and the path of `audit.log`. When an agent invoked the skill
on its own, keep waiting for the process within the same turn and write nothing before the
report: whoever asked, such as the agent that started a subagent, may receive only what the
turn ends with.

The report is `report.md`. On a non-zero exit or an empty `report.md`, write no note: say
that the audit failed and give its cause in plain words with the path of the file it comes
from, the end of `audit.log`, or `report.md` for Claude, which prints its errors there.
