# massdo-skills is released through its manifests, not the journal

The plugins that talk to the journal server publish a `version_hash` that the server compares. `massdo-skills` is an independent style plugin with no journal integration. `docs/massdo-skills-independence-audit.md` is the audit made before that integration was removed. `massdo-skills` keeps a release document with a version and a changelog, without a journal identity hash, and the publisher does not send its release to the journal server.

`RELEASE_NAMES` leaves `massdo-skills` out of the releases it discovers. Validation rejects any reference to Nestor, `version_hash` or the journal host inside `plugins/massdo-skills` and `plugins/thoth`.

Code:

- `scripts/publish_plugin_releases.py`: `RELEASE_NAMES`
- `scripts/validate.py`: the release document keys and the standalone plugin scan
