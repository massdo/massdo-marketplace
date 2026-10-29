# Audit brief

The auditor starts from the brief alone. It holds only the stored content of the audited
work and the audit instructions, never this conversation or an opinion of the work, whether
the calling agent's or that of whoever asked for the audit. The branch file gives the
content proper to the audited work; this file completes the brief with what every audit
shares.

## Common fields

- The repository, the mode and the pinned SHAs.
- The language of the report, named explicitly: the user's language or, when an agent asked
  for the audit, the language that agent names, otherwise the language of its request.

## Code mode

In code mode, the brief asks the auditor to check `git diff <base> <head>` against the
reference that the branch file names: criteria not met, bugs and regressions, missing or
weakened tests, and changes outside the scope.

## Auditor rules

In every mode, the brief gives the auditor these rules:

- Stay read-only: no file, commit, push, pull request comment or journal entry.
- Read the code through Git at the given SHAs (`git show`, `git grep`, `git diff`), never
  in the working tree, which may hold unrelated local changes.
- Ask no question.
- End with a last message that is the report alone, written in the language that the brief
  names, in three blocks titled in that language, such as ISSUES, EXAMPLE and SOLUTIONS in
  English or ENJEUX, EXEMPLE and SOLUTIONS in French: one line per issue, the most important
  first; a single concrete example in two or three sentences; numbered solutions, one
  imperative action per line. No file paths and no detailed evidence. Keep only the issues
  that occur in the nominal flow, never one built on an unfavorable scenario that nothing
  establishes. Without any issue, a single line under the first heading says so.
