# A version bump changes the changelog and the hash

The changelog is what a client shows for the new version. The hash is what the journal server compares to tell whether a client is current. When a release document changes its version against the baseline, its changelog must change too, and so must its `version_hash`.

A bump that keeps the previous changelog would describe the wrong release, and a bump that keeps the hash would tell outdated clients they are current; validation refuses both. The hash rule does not apply to `massdo-skills`, which has no hash.

Code:

- `scripts/validate.py`: the comparison of `release` with `published`, the baseline version of `plugin-release.json`
