# Skill frontmatter accepts client extensions and rejects duplicate keys

Skills are shared by several clients, and some clients add their own frontmatter fields on purpose. A YAML mapping with a duplicate key otherwise keeps the last value silently, so the field being checked could be replaced without notice. `scripts/validate_skills.py` validates the shared fields and does not reject unknown ones. It loads YAML with `UniqueKeyLoader`, which refuses duplicate keys.

A new client-specific field needs no change to the validator. A frontmatter that repeats a key fails validation.

Code:

- `scripts/validate_skills.py`: `validate_skill` and `UniqueKeyLoader`
