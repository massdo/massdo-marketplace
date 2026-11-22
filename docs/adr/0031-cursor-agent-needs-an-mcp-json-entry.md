# Cursor Agent gets an entry in ~/.cursor/mcp.json, remembered by a marker

Cursor Agent only connects to servers listed in `~/.cursor/mcp.json`, so the plugin copy alone is invisible to it. `install.sh` adds the Nestor entry to that file once and remembers it with a marker file. `uninstall.sh` removes the entry only when that marker is present.

An entry the user added by hand is never removed. The installer test double reads the same file to decide whether Cursor Agent knows the server.

Code:

- `install.sh`: `cursor_add_server`
- `uninstall.sh`: `cursor_remove_server`
- `tests/fixtures/installer_client.py`: `cursor_server_configured`
