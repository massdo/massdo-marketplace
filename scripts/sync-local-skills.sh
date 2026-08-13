#!/bin/sh
set -eu

repo_root=$(git rev-parse --show-toplevel)

npx --yes skills@latest add "$repo_root" \
  --skill nestor-journal \
  --global \
  --agent codex \
  --agent claude-code \
  --yes

