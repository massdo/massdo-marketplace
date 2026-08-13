#!/bin/sh
set -eu

npx --yes skills@latest add massdo/nestor-plugins \
  --skill nestor-journal \
  --global \
  --agent codex \
  --agent claude-code \
  --agent cursor \
  --yes

