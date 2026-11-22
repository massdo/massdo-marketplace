# Repository fields of a skill live in its metadata map

`pluginVersion` belongs to this repository, not to Agent Skills. The Agent Skills frontmatter offers a `metadata` map, whose values are strings. A namesake skill declares `pluginVersion` inside `metadata`, never as a top-level frontmatter field.

Validation fails when `pluginVersion` or `antipattern` appears at the top level of the frontmatter of a namesake skill.

Code:

- `scripts/validate.py`: the frontmatter checks of the namesake skill
