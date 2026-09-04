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

`plugins/nestor/plugin-release.json` is the public version-and-changelog document. The journal server reads it without authentication.

- Format: `{ "version": "X.Y.Z", "changelog": "1–3 user-facing lines" }`. No commit list. No internal ticket number.
- Address: `https://raw.githubusercontent.com/massdo/massdo-marketplace/main/plugins/nestor/plugin-release.json`
- Service: GitHub raw on `main`. Override the address with `JOURNAL_PLUGIN_RELEASE_URL` on the server.
- Maximum size: 4096 bytes. A larger document is treated as unreadable.

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
python3 scripts/validate.py
```

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.
