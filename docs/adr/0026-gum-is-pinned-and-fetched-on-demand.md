# gum is pinned and downloaded only when the wizard must ask

The spinners and the sign-in question are drawn by gum (charmbracelet/gum). The installers already pin jq by version and SHA-256. gum is pinned by version and SHA-256 like jq. It is downloaded only when the setup command has to ask which apps to set up; a run with `--client` never downloads it. `uninstall.sh` pins the same tool; it is only needed to ask which apps to clean.

Both scripts carry the same `gum_version` and the same checksums; no check compares them.

Code:

- `install.sh`: `ensure_gum`
- `uninstall.sh`: `ensure_gum`
