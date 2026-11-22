# A skill is reached one way: by its own name

A command wrapper that inlines a skill gives the same instructions a second entry point. Claude Code then counts the skill twice in the menu and in `plugin details`, while Codex never sees the wrapper at all. Cursor and Claude Code find commands by convention, from the directory. No manifest declares `commands`, and no plugin ships a commands directory.

Validation checks the manifests and the directory: dropping the declaration without dropping the files would quietly restore the duplicate.

Code:

- `scripts/validate.py`: the check that `manifest.get("commands")` is absent, and the directory check that follows it
