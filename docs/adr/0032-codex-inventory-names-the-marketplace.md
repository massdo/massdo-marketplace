# The Codex plugin inventory names the marketplace

Without a marketplace name, `codex plugin list` also refreshes its remote plugin catalog, which can take longer than the installer's time budget on a cold cache. For Codex, `install.sh` and `install.ps1` call `plugin list --json -m massdo-marketplace`.

Codex lists that marketplace alone and skips its remote catalog refresh. The test double filters by `-m` the same way, and `test_codex_inventory_names_the_marketplace` checks the call.

Code:

- `install.sh`: `plugin_state`
- `install.ps1`: `Read-Plugins`
- `tests/fixtures/installer_client.py`: the `plugin list` branch
- `tests/test_install.py`: `test_codex_inventory_names_the_marketplace`
