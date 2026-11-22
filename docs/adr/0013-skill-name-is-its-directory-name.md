# A skill's declared name is its directory name

Agent Skills requires the declared name to be the directory name, and every client resolves an invocation through the directory. Validation fails when the `name` of a `SKILL.md` differs from the name of its directory.

Without the rule, a mismatch would make `/<plugin>:<name>` reach nothing while the skill still looks present.

Code:

- `scripts/validate.py`: the check on `declared.group("name")`
- `scripts/validate_skills.py`: `validate_skill`
