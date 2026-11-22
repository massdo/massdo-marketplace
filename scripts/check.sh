#!/bin/sh

set -e

ROOT="$(git rev-parse --show-toplevel)"
PYTHON="${VALIDATION_PYTHON:-python3}"
if [ -z "${VALIDATION_PYTHON:-}" ] && [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
fi

"$PYTHON" "$ROOT/scripts/validate.py" "$@"
"$PYTHON" "$ROOT/scripts/validate_skills.py"
"$PYTHON" "$ROOT/scripts/check_comments.py"

if ! command -v claude >/dev/null 2>&1; then
    if [ "${CI:-false}" = true ]; then
        echo "claude CLI is required in CI." >&2
        exit 1
    fi
    echo "claude CLI not found — skipped the official manifest check."
    exit 0
fi

set +e
failed=0

for plugin in "$ROOT"/plugins/*/; do
    [ -f "$plugin.claude-plugin/plugin.json" ] || continue
    if ! output=$(claude plugin validate "$plugin" --strict 2>&1); then
        printf '%s\n' "$output"
        failed=1
    fi
done

if ! output=$(claude plugin validate "$ROOT/.claude-plugin/marketplace.json" --strict 2>&1); then
    printf '%s\n' "$output"
    failed=1
fi

[ "$failed" -eq 0 ] || exit 1

echo "Official manifest check passed."
