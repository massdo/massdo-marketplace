# Commit hooks validate a snapshot of the index

A commit records the index, which can differ from the working tree when a commit is partial. Git does not invoke `pre-commit` for an automatic merge commit. `scripts/check-commit.sh` checks out the index into a temporary snapshot and runs `check.sh` there, without stashing or changing the user's working tree. The script keeps the history available to `--baseline` and makes every file read use the snapshot (`GIT_DIR`, `GIT_WORK_TREE`, and `check.sh` run from the snapshot); `GIT_INDEX_FILE` is unset since the temporary index of a partial commit is no longer needed there. A `pre-merge-commit` hook runs the same script.

Validation sees exactly what the commit will hold, and a merge commit is validated like any other.

Code:

- `scripts/check-commit.sh`
- `.githooks/pre-commit`
- `.githooks/pre-merge-commit`
