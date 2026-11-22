# The CI takes its baseline from the event

On a pull request, the CI checkout is GitHub's merge tree. A push may contain several commits. `scripts/check-ci.sh` compares the checkout with the pull request's base commit, or with the commit that preceded the push, not with the last commit's parent.

A bad release in the middle of a multi-commit push is caught; comparing just the last commit would miss it, which `test_ci_compares_multi_commit_push_to_before_sha` shows.

Code:

- `scripts/check-ci.sh`
- `tests/test_validation.py`: `test_ci_compares_multi_commit_push_to_before_sha`
