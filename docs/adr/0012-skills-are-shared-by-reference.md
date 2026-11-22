# Skills are shared across ecosystems by reference, never copied

Skills are shared by reference across the ecosystems of a plugin, never copied, so a plugin holds one `SKILL.md` for each skill name.

Two `SKILL.md` files that claim one name inside a plugin mean a stale duplicate, and validation fails.

Code:

- `scripts/validate.py`: `by_name` in the loop over `SKILL.md` files
