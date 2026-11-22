# Every ecosystem of a plugin points at the same MCP server

Cursor reads `mcp.json`; Claude Code and Codex read `.mcp.json`. Kimi Code declares its MCP servers inline in its manifest instead of pointing at a file. These are several declarations of one server. `.mcp.json` and `mcp.json` of a plugin must be equal, and each server of `mcp.json` must be declared by the Kimi Code manifest with the same URL.

A drift between the declarations would send one ecosystem at a dead endpoint; validation fails first.

Code:

- `scripts/validate.py`: the comparison of `dotted` with `plain`, and of `kimi_manifest` with `mcp.json`
