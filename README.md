# Massdo marketplace

This repository is the canonical source for the Nestor journal skill and its Codex, Claude Code, and Cursor plugins.

## Layout

- `plugins/nestor-journal-assistant/skills/nestor-journal/`: shared skill for Codex, Claude Code, and Cursor.
- `plugins/nestor-journal-assistant/.codex-plugin/`: Codex plugin manifest.
- `plugins/nestor-journal-assistant/.claude-plugin/`: Claude Code plugin manifest.
- `plugins/nestor-journal-assistant/.cursor-plugin/`: Cursor plugin manifest.
- `plugins/nestor-journal-assistant/.mcp.json`: Claude Code and Codex public MCP connection.
- `plugins/nestor-journal-assistant/mcp.json`: Cursor public MCP connection.
- `.agents/plugins/marketplace.json`: Codex marketplace catalog.
- `.claude-plugin/marketplace.json`: Claude Code marketplace catalog.
- `.cursor-plugin/marketplace.json`: Cursor marketplace catalog.

## Install the Claude Code plugin

```bash
claude plugin marketplace add massdo/massdo-marketplace
claude plugin install nestor-journal-assistant@massdo-marketplace
```

The Claude manifest omits `version`. Claude Code therefore uses the Git commit SHA as the plugin version.

## Install the Codex plugin from a clone

```bash
codex plugin marketplace add /absolute/path/to/massdo-marketplace
codex plugin add nestor-journal-assistant@massdo-marketplace
```

The public OpenAI plugin is managed separately through the OpenAI submission portal. Published MCP metadata and skill snapshots remain reviewed artifacts. A public skill change requires a new scan, review, and publication.

## Install the Cursor plugin

Load the plugin locally while developing:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s /absolute/path/to/massdo-marketplace/plugins/nestor-journal-assistant \
  ~/.cursor/plugins/local/nestor-journal-assistant
```

Then reload Cursor (**Developer: Reload Window**) and check **Customize** for the skill and MCP server.

Teams and Enterprise can import this repository as a team marketplace from **Dashboard → Plugins → Import from Repo**.

The public Cursor Marketplace listing is submitted separately at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Validate

```bash
python3 scripts/validate.py
```

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.
