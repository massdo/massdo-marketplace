# A path a manifest declares must resolve

A manifest points at its skills, commands, MCP servers, hooks, agents and rules by path. When such a path does not exist, the ecosystem loads nothing. Validation checks that every path a manifest declares exists inside the plugin.

A renamed or deleted directory fails validation until the manifests follow.

Code:

- `scripts/validate.py`: the loop over `skills`, `commands`, `mcpServers`, `hooks`, `agents` and `rules`
