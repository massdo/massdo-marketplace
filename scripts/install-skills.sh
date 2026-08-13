#!/bin/sh
set -eu

npx --yes skills@latest add massdo/massdo-marketplace \
  --skill nestor-journal \
  --global \
  --agent codex \
  --agent claude-code \
  --agent cursor \
  --yes

