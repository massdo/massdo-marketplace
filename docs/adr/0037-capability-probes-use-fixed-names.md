# Capability probes use names fixed in the script

Before setting up Codex or Claude Code, `run_client` runs `<binary> <capability> --help` for four capabilities: `plugin list`, `plugin marketplace list`, `plugin marketplace add` and `mcp login`. The capability is expanded unquoted into the command line. The capability names are a fixed list in `run_client`, never supplied by the caller.

No outside value reaches that unquoted expansion.

Code:

- `install.sh`: the `capability` loop in `run_client`
