# Nestor plugins

This repository is the canonical source for the Nestor journal skill and its Codex and Claude Code plugins.

## Layout

- `plugins/nestor-journal-assistant/skills/nestor-journal/`: shared skill for Codex and Claude Code.
- `plugins/nestor-journal-assistant/.codex-plugin/`: Codex plugin manifest.
- `plugins/nestor-journal-assistant/.claude-plugin/`: Claude Code plugin manifest.
- `plugins/nestor-journal-assistant/.mcp.json`: shared public MCP connection.
- `.agents/plugins/marketplace.json`: Codex marketplace catalog.
- `.claude-plugin/marketplace.json`: Claude Code marketplace catalog.

## Install the shared skill

Install the skill globally for Codex and Claude Code:

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

After each successful `git pull` or merge, the hook reinstalls the checked-out skill for Codex and Claude Code.

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

## Validate

```bash
python3 scripts/validate.py
./scripts/test-npx-skills.sh
./scripts/test-npx-skills.sh massdo/nestor-plugins
```

Never commit MCP tokens, OAuth secrets, reviewer credentials, or local journal data.
