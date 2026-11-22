# The official validator reads Claude Code's files only, and reports every failure

`claude plugin validate` is Claude Code's own validator. The Codex catalog nests its source (`{"source": "local", "path": ...}`) and carries a policy block, so that validator refuses it by design. A local clone used with Codex or Cursor may not have the `claude` CLI. `check.sh` submits only the Claude Code manifests and the Claude Code catalog to the official validator. The `claude` CLI is optional locally and mandatory on the CI runner. The script reports every broken manifest before it fails.

Submitting the Codex catalog would fail the hook on a file that is correct for the ecosystem that reads it. A hook that stopped at the first broken manifest would turn a single fix into as many commit attempts as there are errors.

Code:

- `scripts/check.sh`: the block after the `claude` CLI lookup
