# Codex installs and enables with the same command

In Codex, the native `plugin add` command also enables an existing plugin; it does not run OAuth. For Codex, the wizard runs `plugin add` whether the plugin is missing or only disabled. Claude Code gets `plugin enable` for an installed but disabled plugin and `plugin install` for a missing one.

After the plugin is added, `finish` offers the sign-in, and runs `mcp login` if the user accepts, only when the verification reports that Nestor is not signed in.

Code:

- `install.sh`: the plugin block of `run_client`
