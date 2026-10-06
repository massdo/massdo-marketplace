# Massdo Skills independence audit

Audit of the published 0.11.2 plugin before removing its journal integration.

## References inside the plugin

`rg -n -i 'nestor|version_hash|journal\.mcp-marketplace\.org' plugins/massdo-skills`
returns six lines:

- `skills/answer-short/SKILL.md:18`: sends the plugin hash on Nestor MCP calls.
- `skills/articulate/SKILL.md:18`: the same instruction.
- `skills/chief-of-staff/SKILL.md:21`: the same instruction.
- `skills/extract-signal/SKILL.md:47`: the same instruction.
- `plugin-release.json:3`: publishes the hash used by those instructions.
- `plugin-release.json:4`: redirects users to the Nestor Beta ship skill.

The four manifests and four `agents/openai.yaml` files contain no such references
or MCP dependencies. The plugin has no MCP connection files.

## What maintains the coupling

- `scripts/validate.py` requires a hash in every skill and release document,
  and a new hash when a release version changes.
- `scripts/publish_plugin_releases.py` discovers every release document and
  sends it to the journal server, including this independent plugin.
- `scripts/plugin_release_history.py` expects current releases to have hashes.
- `CLAUDE.md` and the release instructions in `README.md` apply those rules
  to every plugin, so a later release would reintroduce the coupling.

`CLAUDE.md` is ignored local guidance; `README.md` carries the shared release rules.

Published associations remain in the repository-level `plugin-release-history.json`;
they are historical evidence outside the installed plugin.

## Correction checks

The corrected plugin must have no scan matches. Its release document keeps only
`version` and `changelog`. Repository validation must accept a later version bump
without a hash, reject reintroduced references anywhere inside the plugin, and
exclude its current release from journal notifications while retaining history.
