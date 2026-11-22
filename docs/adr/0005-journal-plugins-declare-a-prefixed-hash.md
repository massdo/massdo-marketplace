# Journal plugins declare their identity with a prefixed hash

Each skill of a journal-integrated plugin tells the server which plugin release it comes from, with a `version_hash`. The published hash changes at every release. Why a prefix was needed beyond that is not recorded in the code. The hash a skill declares is its plugin's prefix followed by the published hash: `1` for `nestor`, `2` for `nestor-beta`. The prefix preserves the plugin's identity after the published hash changes. Other plugins keep their existing contract without a prefix. A hooks module that calls Nestor itself sends the same value as the skills of its plugin.

Validation fails when a skill or a `hooks/*.tsx` module declares a hash that is not the prefix plus the hash published in `plugin-release.json`.

Code:

- `scripts/validate.py`: `plugin_hash_prefixes` and the checks on `SKILL.md` and on `VERSION_HASH` in `hooks/*.tsx`
