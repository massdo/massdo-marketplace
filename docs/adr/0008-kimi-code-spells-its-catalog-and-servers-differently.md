# Kimi Code spells its catalog entries and MCP servers differently

Kimi Code names its catalog entries `id` where Codex, Claude Code and Cursor use `name`, and it versions the catalog root. It declares `mcpServers` as an inline server map in its manifest, not as a path to a file the way Codex and Cursor do. The validator reads each ecosystem's catalog through its own spelling, and skips the path check for a manifest value that is an inline map.

`CATALOGS` holds, for each ecosystem, how to read an entry's name and source path. The validation tests build a Kimi Code catalog with `id` entries and a root `version`.

Code:

- `scripts/validate.py`: `CATALOGS` and the loop over the paths a manifest declares
- `tests/test_validation.py`: `RepositoryValidation.setUp`
