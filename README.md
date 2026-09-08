# Massdo marketplace

This repository is the canonical source for the Nestor journal skill and its Codex, Claude Code, and Cursor plugins.

## Layout

- `plugins/nestor/skills/nestor/`: shared journal skill for Codex, Claude Code, and Cursor.
- `plugins/nestor/skills/activity/`: activity timer and time-report skill, exposed as `/nestor:activity` where commands are supported.
- `plugins/nestor/skills/tree/`: shared tree-rendering skill, also exposed as a Claude Code and Cursor command.
- `plugins/nestor/skills/check-for-updates/`: explicit plugin version check, also exposed as `/nestor:check-for-updates`.
- `plugins/nestor/commands/`: Claude Code and Cursor commands.
- `plugins/nestor/.codex-plugin/`: Codex plugin manifest.
- `plugins/nestor/.claude-plugin/`: Claude Code plugin manifest.
- `plugins/nestor/.cursor-plugin/`: Cursor plugin manifest.
- `plugins/nestor/.mcp.json`: Claude Code and Codex public MCP connection.
- `plugins/nestor/mcp.json`: Cursor public MCP connection.
- `plugins/nestor-beta/`: staging plugin for skills under test, see [Beta staging plugin](#beta-staging-plugin).
- `.agents/plugins/marketplace.json`: Codex marketplace catalog.
- `.claude-plugin/marketplace.json`: Claude Code marketplace catalog.
- `.cursor-plugin/marketplace.json`: Cursor marketplace catalog.

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

## Plugin release document

`plugin-release.json` is a plugin's public version-and-changelog document. The journal server reads it without authentication. Two plugins publish one: `nestor` and `nestor-beta`.

- Format: `{ "version": "X.Y.Z", "version_hash": "16 hex", "changelog": "1–3 user-facing lines" }`. No commit list. No internal ticket number.
- Address: `https://raw.githubusercontent.com/massdo/massdo-marketplace/main/plugins/<name>/plugin-release.json`
- Service: GitHub raw on `main`. Override the address with `JOURNAL_PLUGIN_RELEASE_URL` on the server.
- Maximum size: 4096 bytes. A larger document is treated as unreadable.

### Two documents, one server that reads a single one

The server still compares every `version_hash` it receives against `nestor`'s document alone, because a call carries a hash and no plugin name — the contract `yellow_jackal` settled. `nestor-beta` therefore publishes a release its skills do not yet send: `build` and `spec` keep sending `nestor`'s hash, since sending their own would be rejected as an outdated client on the very next call.

That is deliberate, and it is the state to leave in place until the server is refactored to read the document of the plugin that identifies itself on the call. Until then, `scripts/validate.py` holds the weaker rule that fits both worlds: a hash a skill hard-codes must be published by *some* `plugin-release.json` here. A plugin that ships its own `.mcp.json` is held to the exact match instead, since its skills identify that very plugin.

## Beta staging plugin

`plugins/nestor-beta/` holds skills and commands being written or reworked, so `nestor`
only ever ships what has been tried. It reaches the same three ecosystems and is listed in
the same three catalogs, under its own name.

It declares **no MCP server at all**, in any ecosystem. It adds skills and commands, nothing
else; the journal server comes from `nestor`, which must be installed alongside it.

That is deliberate. Declaring the same server in both plugins would register it twice, and
on Claude Code the Nestor tools would appear under two plugin prefixes: nineteen duplicate
tool definitions in every request, and an instruction like "call `update_item`" no longer
naming one tool. Since a skill can call any server registered for the session, the second
declaration buys nothing.

Claude Code installs `nestor` on its own, from `"dependencies": ["nestor"]` in the Claude
Code manifest. Codex and Cursor have no equivalent field, so install both plugins there.

Iterate without publishing anything, reloading with `/reload-plugins` after each edit:

```bash
claude --plugin-dir /absolute/path/to/massdo-marketplace/plugins/nestor-beta
```

A local plugin directory takes precedence over an installed plugin of the same name for
that session, so this needs no uninstall and no version bump.

### Promote a skill into nestor

A skill leaving this plugin is moved, never copied — one `SKILL.md` per skill name is the
rule the whole repository is built on.

```bash
git mv plugins/nestor-beta/skills/<name> plugins/nestor/skills/<name>
git mv plugins/nestor-beta/commands/<name>.md plugins/nestor/commands/<name>.md
```

Then, in the same commit:

- Rewrite the `/nestor-beta:<name>` invocations inside the skill to `/nestor:<name>`.
- Bump the shared version in the three `nestor` manifests, in `plugin-release.json`, and in
  the `pluginVersion` of `skills/nestor/SKILL.md`.
- Regenerate `version_hash` with `openssl rand -hex 8` and write the changelog line for
  that release. A skill that hard-codes a `version_hash` must carry the new value, or the
  server reports every up-to-date install as outdated.

## Validate

```bash
git config core.hooksPath .githooks   # once per clone, or neither hook below runs
./scripts/check.sh                    # every check this repository has, in one command
```

`scripts/check.sh` runs two validators, and they do not overlap:

- `scripts/validate.py` reads every catalog and manifest against each other — a plugin
  listed in one catalog and missing from another, three manifests disagreeing on a version,
  `.mcp.json` drifting from `mcp.json`, a release tag naming a version its own commit never
  declared. No ecosystem catches that on its own, since each one only ever reads its own
  file.
- `claude plugin validate` reads each Claude Code manifest against Anthropic's published
  schema — the shape no in-repo script can know, since Anthropic owns it and can change it.
  It is skipped when the `claude` CLI is absent, which keeps CI and Codex-only clones green.

Passing one proves nothing about the other: a manifest can be individually valid and still
contradict its catalog entry.

`.githooks/pre-commit` runs `check.sh --baseline HEAD` and refuses the commit when it fails.
CI alone was not enough: this repository takes direct commits on `main`, so a red run
arrives after the push. Never bypass the hook with `--no-verify`.

`.githooks/pre-push` runs the plain `check.sh`. A tag is created after the commit it points
at, so nothing exists for the pre-commit hook to check while that commit is being made: the
push is the last moment a malformed tag is still local.

`--baseline <ref>` adds the one rule the plain run cannot check: a plugin whose version
changed since that commit must also change its changelog, otherwise a client shows the
previous release's text for the new version. It compares the tree being committed against
the commit before it, and only the hook holds both at once: by the time CI runs, that tree
*is* `HEAD`, so `--baseline HEAD` would compare a release to itself. The workflow keeps
running the plain `validate.py`.

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
- **Cursor** — no published schema was found. `.cursor-plugin/*.json` follows the shape Cursor's
  documentation describes, and nothing in this repository validates it.

Two consequences are easy to trip over.

**`argument-hint` is not a skill field.** It belongs to Claude Code commands and to Codex's
custom prompts — the `/` surface, which also takes `$1`…`$9` and `$ARGUMENTS`. Codex invokes
*skills* with `$`, has no `commands` key in its manifest, and never reads `commands/`, so it
shows no argument hint for a skill. `interface.default_prompt` in `agents/openai.yaml` is the
closest thing, which is why the skills here spell their arguments out in that string.

**Codex does not honour `disable-model-invocation` on its own.** `agents/openai.yaml` with
`policy.allow_implicit_invocation: false` is what actually holds there, and it still permits the
explicit `$skill` invocation — which is exactly the intent for a command-backed skill.

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

The format is checked now rather than merely agreed. `scripts/validate.py` reads every tag
in the clone back against the commit it points at, and fails on a name that is not
`<plugin>--v<version>` or on a version that commit does not declare. `.githooks/pre-push`
runs the checks before a tag can leave the machine, and CI clones the full history so a
clone whose hooks were never configured is covered too. `claude plugin validate` cannot
help here: it reads a manifest against the official schema and knows nothing about tags.

Tags here are informational: no client resolves a version from one. The journal server resolves the published
version from `plugin-release.json` on `main`, and each ecosystem reads the `version` in its
own manifest. A missing tag breaks nothing, so a tag never substitutes for a version bump —
`nestor` 0.4.6 shipped untagged.
