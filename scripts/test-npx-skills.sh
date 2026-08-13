#!/bin/sh
set -eu

repo_root=$(git rev-parse --show-toplevel)
source=${1:-$repo_root}
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nestor-skills-test.XXXXXX")
trap 'rm -rf "$test_root"' EXIT INT TERM

git -C "$test_root" init --quiet
cd "$test_root"

npx --yes skills@latest add "$source" \
  --skill nestor-journal \
  --agent codex \
  --agent claude-code \
  --yes

test -f "$test_root/.agents/skills/nestor-journal/SKILL.md"
test -f "$test_root/.claude/skills/nestor-journal/SKILL.md"

npx --yes skills@latest list --json | grep -q 'nestor-journal'

if [ "$source" != "$repo_root" ]; then
  update_log="$test_root/update.log"
  npx --yes skills@latest update nestor-journal --project --yes | tee "$update_log"
  ! grep -q 'No installed skills found' "$update_log"
fi
