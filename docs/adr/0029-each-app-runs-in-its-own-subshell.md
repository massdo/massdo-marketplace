# Each app is set up in its own subshell

The wizard sets up several apps in one run. A failure on one app must not end the run for the others. `run_client` runs in a subshell for each app. `fail`, `incomplete`, `succeed` and the guided result end that app only, and the exit code of the subshell becomes the app's result in the summary. `uninstall.sh` removes each app in a subshell the same way.

`succeed`, `incomplete` and `guide_client` call `exit` and are only called inside the per-app subshell. `fail` also calls `exit`: inside the per-app subshell it ends that app; at the top level (argument parsing, the start-up checks before the per-app loop, `ensure_jq`, `ensure_gum`, `choose_clients`) it ends the whole run; inside the command substitutions of `inventory` it ends only that substitution, and the menu shows a state instead.

Code:

- `install.sh`: `succeed`, `incomplete`, `fail`, `run_client`
- `uninstall.sh`: `remove_client`
