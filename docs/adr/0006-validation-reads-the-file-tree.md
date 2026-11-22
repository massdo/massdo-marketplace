# Validation reads the file tree and resolves its baseline once

A release is published by the file tree alone. Some checks compare the tree with an earlier commit, given by `--baseline`. Every check reads the file tree. The baseline reference is resolved to a commit once, at the start, and the script stops when it does not name an available commit.

A baseline that names no available commit never disables the checks that depend on it: the run fails instead.

Code:

- `scripts/validate.py`: the argument parsing and the resolution of `BASELINE`
