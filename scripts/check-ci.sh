#!/bin/sh
# The PR checkout is GitHub's merge tree; a push may contain several commits.
set -eu
export CI=true
root=$(git rev-parse --show-toplevel)
case "${GITHUB_EVENT_NAME:-}" in
    pull_request) baseline=${PR_BASE_SHA:-} ;;
    push)
        baseline=${PUSH_BEFORE_SHA:-}
        if [ "$baseline" = 0000000000000000000000000000000000000000 ] &&
           [ "${PUSH_CREATED:-false}" = true ]; then
            echo 'First push: no previous release to compare.'
            exec "$root/scripts/check.sh"
        fi
        ;;
    *) echo 'Unsupported validation event.' >&2; exit 1 ;;
esac
[ -n "$baseline" ] || { echo 'Missing validation baseline.' >&2; exit 1; }
exec "$root/scripts/check.sh" --baseline "$baseline"
