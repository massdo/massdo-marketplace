# Validation tests run real Git and stub only the CLI boundary

The validation scripts work on Git history, hooks and the `claude` CLI. The publisher sends releases over HTTP. The tests build real repositories with real commits and merges, and run the same entry points as the CI. In `RepositoryValidation`, only the `claude` CLI is a stub. A commit that the active hooks would refuse is built with `git commit-tree`, the way a clone without hooks would produce it, without bypassing the hooks. The test of a missing `claude` CLI restricts `PATH` so a real installation cannot mask it. The publisher tests send to a real local HTTP server. Their `setUp` patches `ROOT` and `RELEASE_NAMES`; `test_independent_releases_are_not_discovered_but_keep_published_history` imports the publisher inside the fixture repository instead, to exercise its real discovery, not the patched names.

Code:

- `tests/test_validation.py`: `RepositoryValidation`
- `tests/test_publish_plugin_releases.py`
