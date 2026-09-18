#!/bin/sh
# Check exactly the index without stashing or changing the user's worktree.
set -eu

root=$(git rev-parse --show-toplevel)
git_dir=$(git rev-parse --absolute-git-dir)
cd "$root"
if [ -z "${VALIDATION_PYTHON:-}" ]; then
    if [ -x "$root/.venv/bin/python3" ]; then
        VALIDATION_PYTHON="$root/.venv/bin/python3"
    else
        VALIDATION_PYTHON=$(command -v python3)
    fi
fi
export VALIDATION_PYTHON

snapshot=$(mktemp -d "${TMPDIR:-/tmp}/marketplace-index.XXXXXX")
trap 'rm -rf -- "$snapshot"' EXIT
trap 'exit 1' HUP INT TERM
git checkout-index --all --prefix="$snapshot/"

# Keep history available to --baseline, but make every file read use the index
# snapshot. A partial commit's temporary index is no longer needed here.
unset GIT_INDEX_FILE
export GIT_DIR="$git_dir" GIT_WORK_TREE="$snapshot"
cd "$snapshot"
if baseline=$(git rev-parse --verify HEAD 2>/dev/null); then
    "$snapshot/scripts/check.sh" --baseline "$baseline"
else
    echo 'Initial commit: no previous release to compare.'
    "$snapshot/scripts/check.sh"
fi
