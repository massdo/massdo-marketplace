#!/bin/sh

# Every check this repository has, in one command.
#
# Two validators run here, and they do not overlap:
#
#   scripts/validate.py     reads every catalog and manifest against each other.
#                           That is the failure no ecosystem can catch on its
#                           own, since each one only ever reads its own file.
#
#   claude plugin validate  reads one Claude Code manifest against the official
#                           schema. That is the shape no in-repo script can
#                           know, since Anthropic owns it and can change it.
#
# A manifest can be individually valid and still contradict its catalog entry,
# so passing one proves nothing about the other.
#
# Arguments are forwarded to validate.py, so `check.sh --baseline HEAD` works.

set -e

ROOT="$(git rev-parse --show-toplevel)"

python3 "$ROOT/scripts/validate.py" "$@"

# The official validator ships with Claude Code, so it is missing from CI and
# from a clone made to work on Codex or Cursor. Skipping keeps those green
# rather than red for a tool they were never expected to install: the manifests
# stay covered by validate.py, which needs nothing but Python.
if ! command -v claude >/dev/null 2>&1; then
    echo "claude CLI not found — skipped the official manifest check."
    exit 0
fi

# Claude Code's own files only. The Codex catalog nests its source
# ({"source": "local", "path": ...}) and carries a policy block, so this
# validator refuses it by design — submitting it here would fail the hook on a
# file that is correct for the ecosystem that actually reads it.
set +e
failed=0

for plugin in "$ROOT"/plugins/*/; do
    [ -f "$plugin.claude-plugin/plugin.json" ] || continue
    if ! output=$(claude plugin validate "$plugin" 2>&1); then
        printf '%s\n' "$output"
        failed=1
    fi
done

if ! output=$(claude plugin validate "$ROOT/.claude-plugin/marketplace.json" 2>&1); then
    printf '%s\n' "$output"
    failed=1
fi

# Report every broken manifest at once. A hook that stops at the first one
# turns a single fix into as many commit attempts as there are errors.
[ "$failed" -eq 0 ] || exit 1

echo "Official manifest check passed."
