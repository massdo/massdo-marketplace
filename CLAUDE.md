# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A plugin marketplace, not an application. It contains no runtime code — only manifests, catalogs, and Markdown skills that three different agent ecosystems (Codex, Claude Code, Cursor) read to install the same plugins. There is no build, no test suite, and no dependency install.

## Commands

```bash
python3 scripts/validate.py   # the only check; CI runs it on every PR and push to main (Python 3.13)
```

An untracked, gitignored `package.json` holds local convenience scripts (`install-plugin:nestor-journal`, `update-plugin:nestor-journal`) that wrap `npx skills@latest`. It is deliberately not committed — do not add it to git.

## Architecture

### One plugin, three ecosystems

Each plugin lives once under `plugins/<name>/` and is exposed to each ecosystem through a parallel set of files. For `nestor-journal-assistant`:

| Ecosystem | Root catalog | Plugin manifest | MCP config |
|---|---|---|---|
| Codex | `.agents/plugins/marketplace.json` | `.codex-plugin/plugin.json` | `.mcp.json` |
| Claude Code | `.claude-plugin/marketplace.json` | `.claude-plugin/plugin.json` | `.mcp.json` |
| Cursor | `.cursor-plugin/marketplace.json` | `.cursor-plugin/plugin.json` | `mcp.json` |

A change to the plugin's identity (name, description, MCP URL) usually has to be applied in several of these files at once. `scripts/validate.py` exists precisely to catch a half-applied change.

The catalogs are *not* interchangeable, despite looking similar:
- Codex nests the source: `"source": { "source": "local", "path": "./plugins/..." }` and carries a `policy` block.
- Claude Code and Cursor use a plain string source; Cursor nests its description under `metadata`.

### Deliberate asymmetries — do not "fix" these

- **`.mcp.json` and `mcp.json` are two files with identical content.** Cursor reads the unprefixed name, Claude Code and Codex read the dotted one. Both must point at the same URL (`https://journal.mcp-marketplace.org/mcp`); validate.py asserts it.
- **The Claude manifest has no `version` field**, while the Codex and Cursor manifests pin `0.1.0`. Claude Code falls back to the Git commit SHA as the version. validate.py asserts `version` stays absent.
- **Exactly one `SKILL.md` may exist in the whole repo.** validate.py fails on any second one, which blocks copying or snapshotting a skill into another directory. Skills are shared by reference, never duplicated.
- **`massdo-skills` is Claude-Code-only.** It has only a `.claude-plugin/` manifest and appears only in the Claude catalog. Adding it to the Codex or Cursor catalogs would require manifests that do not exist.

### Validation scope

`scripts/validate.py` is a flat script of `assert` statements, not a generic schema validator. It hardcodes `nestor-journal-assistant` and indexes `plugins[0]` in every catalog. **Reordering a catalog's `plugins` array, or adding a plugin before the nestor entry, will break it.** It also scans every file in the repo for a bearer-token authorization header as a crude secret guard — note this catches the literal string anywhere, including in documentation, so describe such headers rather than quoting them.

If you add a second cross-ecosystem plugin, the script must be generalized rather than extended with more index-based asserts.

## Distribution

Installs go through `npx skills@latest`, which writes the canonical copy to `~/.agents/skills/<skill>/`. Codex and Cursor read that directory directly; Claude Code gets a symlink at `~/.claude/skills/<skill>`. An install made from a local path records `source: null` and can never be `update`d — always install from the `massdo/massdo-marketplace` GitHub source so future updates work.

The public OpenAI and Cursor Marketplace listings are submitted through separate portals. A change to a published skill requires a new scan, review, and publication there — merging to `main` does not ship it.
