# Nestor plugins

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

## Install the shared skill

Install the skill globally for Codex, Claude Code, and Cursor:

```bash
./scripts/install-skills.sh
```

Update a tracked installation from GitHub:

```bash
./scripts/update-skills.sh
```

`npx skills update` tracks the skill folder hash. It does not require a plugin version bump.

## Enable automatic local synchronization

Enable the repository's opt-in Git hook:

```bash
./scripts/enable-hooks.sh
```

After each successful `git pull` or merge, the hook runs `npx skills update`. It installs the GitHub skill first when needed.

## Install the Claude Code plugin

```bash
claude plugin marketplace add massdo/nestor-plugins
claude plugin install nestor-journal-assistant@nestor-plugins
```

The Claude manifest omits `version`. Claude Code therefore uses the Git commit SHA as the plugin version.

## Install the Codex plugin from a clone

```bash
codex plugin marketplace add /absolute/path/to/nestor-plugins
codex plugin add nestor-journal-assistant@nestor-plugins
```

The public OpenAI plugin is managed separately through the OpenAI submission portal. Published MCP metadata and skill snapshots remain reviewed artifacts. A public skill change requires a new scan, review, and publication.

## Install the Cursor plugin

Load the plugin locally while developing:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s /absolute/path/to/nestor-plugins/plugins/nestor-journal-assistant \
  ~/.cursor/plugins/local/nestor-journal-assistant
```

Then reload Cursor (**Developer: Reload Window**) and check **Customize** for the skill and MCP server.

Teams and Enterprise can import this repository as a team marketplace from **Dashboard → Plugins → Import from Repo**.

The public Cursor Marketplace listing is submitted separately at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Validate

```bash
python3 scripts/validate.py
./scripts/test-npx-skills.sh
./scripts/test-npx-skills.sh massdo/nestor-plugins
```

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.
