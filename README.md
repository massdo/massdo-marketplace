# Massdo marketplace

This repository is the canonical source for the Nestor journal skill and its Codex, Claude Code, and Cursor plugins.

## Layout

- `plugins/nestor/skills/nestor/`: shared journal skill for Codex, Claude Code, and Cursor.
- `plugins/nestor/skills/tree/`: shared tree-rendering skill, also exposed as a Claude Code and Cursor command.
- `plugins/nestor/skills/check-for-updates/`: explicit plugin version check, also exposed as `/nestor:check-for-updates`.
- `plugins/nestor/commands/`: Claude Code and Cursor commands.
- `plugins/nestor/.codex-plugin/`: Codex plugin manifest.
- `plugins/nestor/.claude-plugin/`: Claude Code plugin manifest.
- `plugins/nestor/.cursor-plugin/`: Cursor plugin manifest.
- `plugins/nestor/.mcp.json`: Claude Code and Codex public MCP connection.
- `plugins/nestor/mcp.json`: Cursor public MCP connection.
- `.agents/plugins/marketplace.json`: Codex marketplace catalog.
- `.claude-plugin/marketplace.json`: Claude Code marketplace catalog.
- `.cursor-plugin/marketplace.json`: Cursor marketplace catalog.

## Install the Claude Code plugin

```bash
claude plugin marketplace add massdo/massdo-marketplace
claude plugin install nestor@massdo-marketplace
```

The Claude manifest omits `version`. Claude Code therefore uses the Git commit SHA as the plugin version.

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

## Validate

```bash
python3 scripts/validate.py
```

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.
