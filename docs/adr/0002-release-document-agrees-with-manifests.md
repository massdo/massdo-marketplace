# A release document agrees with its manifests, and its presence is the trigger

A plugin publishes a release through `plugin-release.json`. A plugin can publish a release without shipping a skill named after it. A skill named after its plugin is the installable plugin itself. The release document is what triggers the release checks, not a namesake skill. When the document exists, its version must be the version the manifests agree on. A plugin that ships a namesake skill must have a release document, and `massdo-skills` must always have one.

The document holds exactly `version`, `changelog` and `version_hash`; `massdo-skills` holds no `version_hash` (see the ADR on its independence from the journal). The changelog holds one to three non-empty lines and the file is at most 4096 bytes.

Code:

- `scripts/validate.py`: the block that reads `release_path` for each plugin
