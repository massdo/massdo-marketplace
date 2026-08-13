#!/bin/sh
set -eu

repo_root=$(git rev-parse --show-toplevel)

if npx --yes skills@latest list --global --json | grep -q 'nestor-journal'; then
  npx --yes skills@latest update nestor-journal --global --yes
else
  "$repo_root/scripts/install-skills.sh"
fi
