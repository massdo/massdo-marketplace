# One command runs complementary validators

`scripts/validate.py` reads every catalog and manifest against each other: that is the failure no ecosystem can catch on its own, since each one only ever reads its own file. `scripts/validate_skills.py` parses the shared skill frontmatter as YAML. `claude plugin validate` reads one Claude Code manifest against the official schema: that is the shape no in-repo script can know, since Anthropic owns it and can change it. A manifest can be individually valid and still contradict its catalog entry, so passing one validator proves nothing about the other. `scripts/check.sh` runs these validators, together with `scripts/check_comments.py`, and the hooks and the CI call that one command.

Arguments are forwarded to `validate.py`, so `check.sh --baseline HEAD` works.

Code:

- `scripts/check.sh`
