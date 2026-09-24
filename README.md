# Massdo marketplace

This repository is the canonical source for the Nestor journal skill and its Codex, Claude Code, Cursor, and Kimi Code plugins.

## Layout

- `plugins/nestor/skills/nestor/`: shared journal skill for Codex, Claude Code, and Cursor.
- `plugins/nestor/skills/activity/`: activity timer and time-report skill.
- `plugins/nestor/skills/tree/`: shared tree-rendering skill.
- `plugins/nestor/skills/check-for-updates/`: explicit plugin version check.
- `plugins/nestor/.codex-plugin/`: Codex plugin manifest.
- `plugins/nestor/.claude-plugin/`: Claude Code plugin manifest.
- `plugins/nestor/.cursor-plugin/`: Cursor plugin manifest.
- `plugins/nestor/.kimi-plugin/`: Kimi Code plugin manifest, with the MCP server inline.
- `plugins/nestor/.mcp.json`: Claude Code and Codex public MCP connection.
- `plugins/nestor/mcp.json`: Cursor public MCP connection.
- `plugins/nestor-beta/`: staging plugin for skills under test, see [Beta staging plugin](#beta-staging-plugin).
- `.agents/plugins/marketplace.json`: Codex marketplace catalog.
- `.claude-plugin/marketplace.json`: Claude Code marketplace catalog.
- `.cursor-plugin/marketplace.json`: Cursor marketplace catalog.
- `.kimi-plugin/marketplace.json`: Kimi Code marketplace catalog.

## Install the Claude Code plugin

```bash
claude plugin marketplace add massdo/massdo-marketplace
claude plugin install nestor@massdo-marketplace
```

Every manifest a plugin ships pins the same `version`, so pushing commits ships nothing until that number changes: Claude Code resolves a version from `plugin.json` first and leaves each install on its cached copy while the number is unchanged.

## Install the Codex plugin from a clone

```bash
codex plugin marketplace add /absolute/path/to/massdo-marketplace
codex plugin add nestor@massdo-marketplace
```

The public OpenAI plugin is managed separately through the OpenAI submission portal. Published MCP metadata and skill snapshots remain reviewed artifacts. A public skill change requires a new scan, review, and publication.

## Install the Cursor plugin

Load the plugin locally while developing:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s /absolute/path/to/massdo-marketplace/plugins/nestor \
  ~/.cursor/plugins/local/nestor
```

Then reload Cursor (**Developer: Reload Window**) and check **Customize** for the skill and MCP server.

Teams and Enterprise can import this repository as a team marketplace from **Dashboard → Plugins → Import from Repo**.

The public Cursor Marketplace listing is submitted separately at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Install the Kimi Code plugin

Kimi Code reads its own manifest and installs from a local clone, in the TUI:

```
/plugins install /absolute/path/to/massdo-marketplace/plugins/nestor
/reload
```

Install `nestor-beta` and `massdo-skills` the same way, or browse all three through the
catalog with `/plugins marketplace /absolute/path/to/massdo-marketplace/.kimi-plugin/marketplace.json`.
Plugins are installed per-user and apply to every project; a session picks up a change after
`/reload` or in a new session. `nestor-beta` declares no MCP server here either — the journal
server comes from `nestor`, which must be installed alongside it.

## Invoke a skill

Every skill here is reached by its own name, and by nothing else. There is no command
wrapper: one `SKILL.md` is the whole surface, so a skill appears once in a menu instead of
twice, and Codex sees the same entry point as Claude Code.

| Ecosystem | Explicit invocation | Arguments |
|---|---|---|
| Claude Code | `/<plugin>:<skill> <arguments>` | passed through; see below |
| Cursor | `/` then the skill name | not documented by Cursor |
| Codex | `$<plugin>:<skill>` | free text after the name |
| Kimi Code | `/skill:<skill> <arguments>` | appended as an `ARGUMENTS:` line |

A skill is also reached without naming it, by asking in plain language, unless its
frontmatter turns that off — see the policy table below.

**Arguments.** The arguments are the text written after the skill name. Claude Code
substitutes `$ARGUMENTS`, `$1`…`$9` and named placeholders when the body contains them, and
otherwise appends a final `ARGUMENTS: <input>` line to the injected content. No `SKILL.md`
here writes a placeholder: each one describes its arguments in portable prose instead, so
the same text works in a client that passes the input some other way, or that passes none
and leaves the request in the user's own message.

**Invocation policy.** Two frontmatter keys decide who may start a skill, and the two
ecosystems do not read the same one:

| Skill | Model may invoke | Held by |
|---|---|---|
| `nestor`, `activity`, `tree`, `check-for-updates` | yes | nothing to set |
| the three `massdo-skills`, `build`, `spec`, `doctor`, `clean-task`, `next-tasks` | no | `disable-model-invocation: true`, and `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |

Codex does not honour `disable-model-invocation`; `agents/openai.yaml` is what holds there,
and it still permits the explicit `$<plugin>:<skill>` invocation. Cursor documents
`disable-model-invocation` and reads it. Kimi Code reads it too, in the same kebab-case
spelling. `user-invocable: false` is never set here: combined
with `disable-model-invocation` it leaves a skill that nothing can reach, and `validate.py`
refuses it.

## Plugin release document

`plugin-release.json` is a plugin's public version-and-changelog document. The journal server reads it without authentication. Every plugin that ships a skill publishes one — today `massdo-skills`, `nestor` and `nestor-beta` — and `scripts/publish_plugin_releases.py` sends every document it finds.

- Format: `{ "version": "X.Y.Z", "version_hash": "16 hex", "changelog": "1–3 user-facing lines" }`. No commit list. No internal ticket number.
- Address: `https://raw.githubusercontent.com/massdo/massdo-marketplace/main/plugins/<name>/plugin-release.json`
- Service: GitHub raw on `main`. Override the address with `JOURNAL_PLUGIN_RELEASE_URL` on the server.
- Maximum size: 4096 bytes. A larger document is treated as unreadable.

### Several documents, one release set

The server reads the documents as a **set**, not one of them. `validatePluginReleaseSet`
refuses a set whose names or hashes repeat, and `resolvePluginRelease` then finds the entry
whose hash matches the one the call carries — so the hash alone identifies the plugin, and a
call needs to name none. `probe_plugin_version` and the update warning both resolve that way.

Two consequences:

- Every skill of every plugin hard-codes the hash of the plugin that **ships** it,
  whatever plugin declares the MCP server it calls — a skill that sends none leaves the
  server unable to tell an outdated install that it is outdated. `nestor-beta` declares no
  server and still publishes its own release, so each of its skills sends `nestor-beta`'s
  hash. `scripts/validate.py` refuses any skill without a hash, in every plugin.
- A version bump must regenerate `version_hash` with `openssl rand -hex 8`, and the new
  value must collide with no other published release. Reusing a hash makes the server
  resolve the wrong plugin; keeping the old one makes it report an outdated client as
  current. `--baseline` refuses a bump that changes neither the hash nor the changelog.

## Beta staging plugin

`plugins/nestor-beta/` holds skills being written or reworked, so `nestor`
only ever ships what has been tried. It reaches the same three ecosystems and is listed in
the same three catalogs, under its own name.

It declares **no MCP server at all**, in any ecosystem. It adds skills, nothing
else; the journal server comes from `nestor`, which must be installed alongside it.

That is deliberate. Declaring the same server in both plugins would register it twice, and
on Claude Code the Nestor tools would appear under two plugin prefixes: nineteen duplicate
tool definitions in every request, and an instruction like "call `update_item`" no longer
naming one tool. Since a skill can call any server registered for the session, the second
declaration buys nothing.

Claude Code installs `nestor` on its own, from `"dependencies": ["nestor"]` in the Claude
Code manifest. Codex, Cursor and Kimi Code have no equivalent field, so install both plugins
there.

Iterate without publishing anything, reloading with `/reload-plugins` after each edit:

```bash
claude --plugin-dir /absolute/path/to/massdo-marketplace/plugins/nestor-beta
```

A local plugin directory takes precedence over an installed plugin of the same name for
that session, so this needs no uninstall and no version bump.

### Clean a task body

Invoke `/nestor-beta:clean-task <ref>` in Claude Code or `$nestor-beta:clean-task <ref>`
in Codex. In Cursor, select `clean-task` and supply the reference. Pass one task id,
server-supported id prefix or exact slug. The explicit invocation authorizes a direct
rewrite of that task's body; the skill never starts implicitly.

It removes information only when obsolescence is established, merges true duplicates and
condenses prose while preserving the useful specification and exact commands, links and
markers. Unresolved decisions and contradictions remain and are reported. Other fields
and items are unchanged; an empty or already clean body needs no write. If the content
changes in the meantime, the cleanup is reassessed while preserving the new information.
Shared Nestor tool procedures remain in the `nestor` skill.

### List a project's active tasks

Invoke `/nestor-beta:next-tasks [project]` in Claude Code or
`$nestor-beta:next-tasks [project]` in Codex. In Cursor, select `next-tasks` and supply
the project name. The whole argument is one project name, spaces included; it is
authoritative and is never checked against the repository. Without an argument, the
project name is inferred from the workspace's Git repository — the last segment of the
`origin` URL, or the root directory name when there is no remote.

It reads the project's `active` view through `list_items`: the `todo`, `in_progress` and
`need_review` tasks, subtasks included, with no time bound and no local re-sorting or
volume cap. When that view is empty, it gives the backlog's task count from the same
response and lists the backlog only if the user accepts; an empty backlog is stated
without a question. An exact `get_project` read comes first, and a close match from
`search_project` stands on its own only when the search returns a single result in total;
anything else is confirmed by the user. Nothing is created or modified, and items are
cited the way the `nestor` skill prescribes.

### Audit a project's delivered tasks

Invoke `/nestor-beta:doctor [project]` in Claude Code or `$nestor-beta:doctor [project]`
in Codex. In Cursor, select `doctor` and supply the project name. The whole argument is one
project name, spaces included; it is authoritative and is never checked against the
repository. Without an argument, the project name is inferred from the workspace's Git
repository — the last segment of the `origin` URL, or the root directory name when there is
no `origin` — so a subdirectory or a linked worktree resolves to the same project as the root.

An exact `get_project` read comes first, and a close match from `search_project` stands on
its own only when the search returns a single result in total; several results, none, or no
reliable inferred name all go back to the user for a choice, and nothing is created. The
audit itself is unchanged: open tasks are checked against merged history, closures are
proposed with evidence, and nothing is closed without approval.

### Promote a skill into nestor

A skill leaving this plugin is moved, never copied — one `SKILL.md` per skill name is the
rule the whole repository is built on.

```bash
git mv plugins/nestor-beta/skills/<name> plugins/nestor/skills/<name>
```

Then, in the same commit:

- Rewrite the `/nestor-beta:<name>` invocations inside the skill to `/nestor:<name>`.
- Bump the shared version in the three `nestor` manifests, in `plugin-release.json`, and in
  `metadata.pluginVersion` of `skills/nestor/SKILL.md` — a quoted string, since `metadata`
  maps string keys to string values.
- Regenerate `version_hash` with `openssl rand -hex 8` and write the changelog line for
  that release. The skill hard-codes the hash of the plugin that now ships it, so moving it
  between plugins changes which hash it carries; a stale value makes the server report every
  up-to-date install as outdated.
- Bump `nestor-beta` too, and regenerate its own hash: it just lost a skill, which is a
  change its release document has to describe.

## Validate

```bash
python3 -m venv .venv
.venv/bin/python3 -m pip install -r scripts/requirements-validation.txt
git config core.hooksPath .githooks   # relative path also works in linked worktrees
./scripts/check.sh                    # all marketplace validators
.venv/bin/python3 -m unittest discover -s tests -v
```

Python 3.11+ is required. `check.sh` uses `.venv/bin/python3` when present, otherwise
`python3`; `VALIDATION_PYTHON` can select another interpreter with the pinned dependencies
installed. Create the environment in each worktree that needs one. A missing PyYAML
dependency fails explicitly. Install the optional local Claude validator with Node 22+:

```bash
npm install --global @anthropic-ai/claude-code@2.1.275
```

`scripts/check.sh` runs complementary validators:

- `scripts/validate.py` reads every catalog and manifest against each other — a plugin
  listed in one catalog and missing from another, the manifests disagreeing on a version,
  `.mcp.json` drifting from `mcp.json`, the Kimi Code manifest declaring an MCP URL that
  `mcp.json` does not have. No ecosystem catches that on its own, since each one
  only ever reads its own file.
- `scripts/validate_skills.py` parses every skill's YAML, rejects duplicate keys, and checks
  names, descriptions, directory names, metadata strings and the types of invocation
  options. It accepts the intentional Claude extensions and the existing repository fields.
  It is not a complete Agent Skills, Codex or Cursor runtime certification.
- `claude plugin validate --strict` reads each Claude Code manifest against Anthropic's published
  schema — the shape no in-repo script can know, since Anthropic owns it and can change it.
  A missing CLI is visibly skipped locally and is an error in CI. A green manifest check
  does not establish that the CLI parsed the skill bodies or that a client loaded them.

Passing one proves nothing about the others: a manifest can be individually valid and still
contradict its catalog entry.

Both `.githooks/pre-commit` and `.githooks/pre-merge-commit` run `scripts/check-commit.sh`.
It exports the index to a temporary directory and runs `check.sh` there against the current
HEAD. This checks exactly the proposed commit, including partial commits, without stashing,
changing unstaged edits or allowing untracked files to mask missing committed files. The
temporary tree is removed on exit. An initial commit has no baseline.

An invalid automatic merge is left pending, with HEAD unchanged: fix and commit it or use
`git merge --abort`. Conflict resolutions and `merge --no-commit` finish through pre-commit.
Fast-forwards create no commit and invoke neither hook. Hooks must be activated in each
clone, are not server enforcement, and do not run for a merge made on GitHub. Direct pushes
to `main` are checked by CI after the push. Never bypass hooks with `--no-verify`.

`--baseline <ref>` requires a plugin whose version changed to also change its changelog and
version hash. An unavailable baseline is an error; a new plugin absent from a valid baseline
is allowed. CI fetches history and calls `check-ci.sh`: a PR's merge tree is compared against
its base SHA, and a push against the SHA before the entire push, not just the last commit.
Only a first push with no predecessor explicitly omits that comparison.

CI installs pinned PyYAML and Claude versions, runs the Git/validator regression tests and
all validators, and records tool versions and installation duration in the job log. The
release notification job still depends on successful validation. The tests exercise actual
Git hooks with a stub at the Claude CLI boundary; the final CI validation uses the real CLI.

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.

## Manifest schemas

Each ecosystem owns the shape of the files it reads. None of it is guessed here — these are
the references, and they are worth re-reading before adding a field:

- **Claude Code** — `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` follow
  `https://anthropic.com/claude-code/marketplace.schema.json`, the schema Anthropic's own
  marketplace declares in its `$schema` key. `claude plugin validate` checks a file against it.
- **Codex plugin** — `.codex-plugin/plugin.json` follows
  [plugin-json-spec.md](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md)
  in `openai/codex`. It allows `name`, `version`, `description`, `author`, `homepage`,
  `repository`, `license`, `keywords`, `skills`, `hooks`, `mcpServers`, `apps` and `interface`
  — and nothing else, since validation rejects unsupported fields.
- **Codex skills** — `SKILL.md` frontmatter and `agents/openai.yaml` are specified in
  [Build skills](https://learn.chatgpt.com/docs/build-skills). The frontmatter documents `name`
  and `description` only. `agents/openai.yaml` carries `interface` (`display_name`,
  `short_description`, `icon_small`, `icon_large`, `brand_color`, `default_prompt` — every one a
  string), `policy` (`allow_implicit_invocation`) and `dependencies.tools`.
- **Kimi Code** — `.kimi-plugin/plugin.json` and `.kimi-plugin/marketplace.json` follow
  [Plugins](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html) in the
  Kimi Code documentation. Two shape differences from the other ecosystems: the manifest
  declares `mcpServers` inline as a server map rather than as a path to a file, and the
  catalog names its entries `id` instead of `name`.
- **Cursor** — no published schema was found. `.cursor-plugin/*.json` follows the shape Cursor's
  documentation describes, and nothing in this repository validates it.

Two consequences are easy to trip over.

**`argument-hint` is a Claude Code extension, not a standard field.** Claude Code documents
it in skill frontmatter and `claude plugin validate --strict` accepts it there, so the skills
that take arguments carry it. The Agent Skills specification does not list it: Codex reads
`name` and `description` only and shows no argument hint for a skill, and Cursor does not
document the field. `interface.short_description` and `interface.default_prompt` in
`agents/openai.yaml` are what a Codex user sees instead, which is why they spell the
arguments out. The body of each skill describes its arguments in prose for the same reason —
that is the only place all three ecosystems read.

The same line separates the rest of the frontmatter. Standard: `name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools`. Claude Code extensions used here:
`argument-hint`, `disable-model-invocation`. Repository-specific data goes in `metadata`,
whose values are strings — that is where `pluginVersion` lives, and Claude Code ignores it.

**Codex does not honour `disable-model-invocation` on its own.** `agents/openai.yaml` with
`policy.allow_implicit_invocation: false` is what actually holds there, and it still permits the
explicit `$<plugin>:<skill>` invocation — which is the intent for a user-driven skill.

## Release tags

A release tag is `<name>--v<version>` — **two dashes** — and `claude plugin tag` is the only
thing that should create one:

```bash
claude plugin tag plugins/nestor-beta --dry-run   # show the tag it would create
claude plugin tag plugins/nestor-beta --push      # create it, then push it
```

It derives the name and version from `plugin.json`, refuses to run when the enclosing
marketplace entry disagrees, and gets the separator right.

Never write the tag by hand. This repository carried single-dash tags (`nestor-v0.4.5`)
until 2026-09-07, and the second one was written by copying the first — a hand-written tag
reproduces whatever is already in the log, which is precisely what an unwritten convention
cannot prevent. Both were renamed to the official format on that date.

Tags here are informational: nothing reads them. The journal server resolves the published
version from `plugin-release.json` on `main`, and each ecosystem reads the `version` in its
own manifest. A missing tag breaks nothing, so a tag never substitutes for a version bump —
`nestor` 0.4.6 shipped untagged.
