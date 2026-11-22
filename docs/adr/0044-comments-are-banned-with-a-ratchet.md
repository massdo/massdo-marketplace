# Comments are banned outside plugins, with a ratchet

No check keeps a comment true: the code changes and the comment stays. The delete-comment pass of 2026-11-21 sorted every comment in `scripts/`, `tests/`, `.githooks/`, `install.sh`, `install.ps1` and `uninstall.sh`, deleted the ones that carried nothing and moved the decisions into the ADRs of this directory. `scripts/check_comments.py` now reports every comment and docstring in that scope, and `scripts/check.sh` runs it with the other validators. It exempts the comments a tool reads: a shebang, a directive such as `# type:`, `# noqa`, `# pragma:`, `# shellcheck` or `#requires`, and the docstring of a module that reads `__doc__`.

`scripts/comments-baseline.json` records the text of each comment that remains, for each file, with the number of times it occurs. The check fails on a comment the baseline does not hold. It also fails when the baseline holds a comment that is gone, until `python3 scripts/check_comments.py --lower-baseline` removes the entry. That command only removes entries.

The code under `plugins/` was not sorted in that pass and is outside the rule. Python is read with its tokenizer; shell, PowerShell and C# are read line by line, so a line of a here-document that starts with `#` would be reported as a comment.

Code:

- `scripts/check_comments.py`
- `scripts/comments-baseline.json`
- `scripts/check.sh`
- `tests/test_check_comments.py`
