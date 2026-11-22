# Skills never set user-invocable

`user-invocable: false` hides a skill from the menu. Together with `disable-model-invocation`, it leaves nothing that can reach the skill. Neither field is a portable Agent Skills field. This repository uses `disable-model-invocation` alone and never sets `user-invocable`.

Validation fails on any `SKILL.md` that declares `user-invocable`.

Code:

- `scripts/validate.py`: the check on `user-invocable` in the skill frontmatter
