# One version number releases a plugin in every ecosystem

A plugin ships one manifest for each ecosystem it supports: Codex, Claude Code, Cursor and Kimi Code. Claude Code falls back to the Git commit SHA when a manifest pins no version. Codex, Cursor and Kimi Code pin a version, so a missing version in the Claude Code manifest would drift from the three others. Every manifest of a plugin declares a semver version, and all the manifests of one plugin declare the same number. One shared number releases the four ecosystems at once.

Validation fails when a manifest has no semver version or when the manifests of a plugin disagree. A version change that does not reach every manifest of the plugin fails validation.

Code:

- `scripts/validate.py`: the per-plugin loop, where `versions` is filled and compared
