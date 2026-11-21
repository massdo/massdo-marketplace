---
name: delete-comment
description: Sort every code comment in a path or in the whole repository into tautology, stale, excuse, decision record or functional. Delete the tautologies and the stale ones, file an issue for each hack that a comment excused, move each decision into an ADR, then add a lint rule that bans comments, with a ratchet for those that remain, and measure the lines of code shed. It edits code, files issues and changes the lint configuration. Run only after a direct user invocation, such as /massdo-skills:delete-comment or $massdo-skills:delete-comment; never invoke it autonomously.
argument-hint: "[path, module or section of the code]"
disable-model-invocation: true
---

# Delete comments

Run only after the user explicitly invokes this skill, for example
`/massdo-skills:delete-comment` or `$massdo-skills:delete-comment`. An agent, subagent,
plan, or another skill must not invoke it on the user's behalf.

No check keeps a comment true: the code changes and the comment stays. Sort every comment
in the scope, delete those that carry nothing, move what the others carry to a place that
is maintained, then add a lint rule so the number of comments can only go down.

## Scope

The arguments are the text written after the skill name; depending on the client, they may
arrive on a final `ARGUMENTS: …` line. A scope is one or more paths, a module or a section
of the code. Without one, the scope is the repository in the working directory.

The scope holds the source code the project owns. Leave out generated and vendored code,
lock files, and the fixtures and snapshots that tests compare. Leave out configuration and
data files, such as YAML or environment examples, unless the user names them.

A doc comment, and a docstring that documents code, count as comments. Consecutive comment
lines form one comment, and so does one block comment. The inventory and the report count
comments; the measurements count lines.

Change comments only. Do not fix a hack, rename a symbol or refactor code in this pass,
even when a comment points at an obvious defect.

## Classes

Give each comment exactly one class. Read the code around it first; a comment cannot be
sorted on its text alone.

- **Functional**: a tool reads it, so removing it changes a build, a check or a published
  document. Examples are a shebang, an encoding line, a directive for a linter, a type
  checker, a formatter or a coverage tool, a build tag, a compiler pragma, a
  generated-code marker, a license header the license or the project requires, an
  expectation that a test runner reads, and a doc comment that a tool consumes, such as a
  documentation generator, a type checker, or a generator of a schema, a command-line help
  or an API description. A docstring that the program reads at run time is functional too.
  A directive is functional by its form, even when the project holds no tool that reads it.
- **Tautology**: it repeats what the code already shows, such as the name of the function
  it sits on, the type of a parameter, or the step the next line performs. A doc comment
  that restates a signature is a tautology unless it is functional.
- **Stale**: it describes code, behavior, names or plans that no longer exist. Commented-out
  code is stale, and so is a note about who changed what and when: the version history
  holds both.
- **Excuse**: it admits that the code is worse than it should be and says why this is
  tolerated, such as a workaround, a temporary fix, a shortcut, a silenced error, a `TODO`
  or a `FIXME`. Such a comment lets a hack stay, and the next author copies it.
- **Decision record**: the code is as intended, and the comment says why, where a reader
  of the code alone would not guess it: an approach chosen over a more obvious one, a
  constraint that comes from outside the code, or an invariant other code relies on.

Three tests settle a doubt between two classes:

1. Between tautology and decision record: would a maintainer who reads only the code make
   a wrong change without this comment? If not, it is a tautology.
2. Between excuse and decision record: is the code what the project wants? If the comment
   defends code that should be replaced, it is an excuse.
3. Between stale and the others: check that what the comment names still exists, by
   reading the code and searching for the names it cites. A comment is not stale because
   it names something that can live outside the repository, such as another system.

Split a comment that holds two classes, such as a decision followed by a restatement, and
treat each part by its class. A directive with prose after it keeps the directive, and the
prose that the tool requires as a justification.

A comment that fits none of these classes is unsorted: leave it in place. Unsorted is not
for a doubt. The tests above settle a doubt between two classes, and a comment that tells a
maintainer nothing they need is a tautology.

When a comment contradicts the code and the project's tests or documentation side with the
comment, the code may be the defect. Leave the comment and report a possible defect.

## Method

1. Take the inventory. List every comment in the scope with its file and line. Use a
   tokenizer, a parser or the project's linter for each language when one is available,
   since comment markers also appear inside strings and URLs. Record, before any edit, the
   number of comments and the number of lines that hold only a comment.
2. Sort every comment into a class.
3. Act on each comment by its class:
   - functional: keep it;
   - tautology or stale: delete it;
   - excuse: file an issue, then delete it;
   - decision record: write it into an ADR, then delete it;
   - unsorted: keep it.
4. Run the checks the project defines, such as its formatter, linter, type checker, tests
   and build. A check that passed before the pass must still pass.
5. Add the lint rule and its ratchet.
6. Measure, then report.

On a scope too large for one pass, finish whole files: a file is either fully sorted or
untouched. The ratchet covers the files left for a later pass. Never present a partial pass
as complete.

### Deleting

Deleting a comment must not change behavior. A block that held only a comment may need the
language's empty statement. Remove the whole line when it held only the comment, and the
blank line it leaves doubled. Remove the trailing whitespace a comment leaves at the end of
a line of code.

When a project check fails because a comment is gone, restore the comment: a comment that
a check requires is functional. This holds for a linter that requires a doc comment, and
for one that accepts an empty block only when it holds a comment. In that second case the
empty block is still an excuse: file its issue and keep the comment. List the restored
comments in the limits of the report.

### Excuse: an issue

Never delete an excuse before its issue exists; the comment is the only record of the hack.

File the issue in the tracker the project uses: the one its remote hosts or its
documentation names. Write it in the language of that tracker's issues. Search the tracker
first and add to an open issue that covers the same hack. Write one issue per hack, not per
comment, when several comments excuse the same implementation. The issue holds:

- the file and the symbol concerned, and the code as it is;
- what the comment said, quoted;
- why the implementation is a hack, and what a correct one would do when the code or the
  comment establishes it. Do not invent a design.

When no tracker is reachable, or it refuses the issue, keep the comment and give the issue
text in the report for the user to file.

### Decision record: an ADR

Never delete a decision record before its ADR exists.

Use the project's ADR directory, format and language when it has them. Otherwise create
`docs/adr/` with one numbered file per decision that holds a title, a status, the context,
the decision and its consequences, in the language of the project's documentation. The
status is accepted, since the code applies the decision. Write one ADR per decision, not
per comment, and complete an existing ADR that already covers the decision.

Name the code the decision governs by path and symbol, not by line number, since lines
move. Write only what the comment and the code establish; where the context is unknown, say
so instead of supplying one. Leave no pointer to the ADR in the code: a pointer is a
comment.

### The lint rule and its ratchet

The rule reports every comment in the scope of the pass except the functional ones, even
where the project's lint covers less code today. It knows a functional comment by its form,
such as a position in the file or a directive prefix, and exempts only the forms this pass
kept. The code the pass adds for the rule holds no comment.

Add it to the linter the project already runs: a built-in rule, a plugin the project can
accept, or a small custom rule or script in the project's language. Make the command that
already runs the project's lint, locally and in its CI, run this rule too. Do not add a
second lint tool or a second pipeline for it.

When comments remain in the scope, add a ratchet:

- a baseline file under version control records, for each file, the number of comments
  the rule reports;
- the check fails when a file holds more comments than its baseline, and when a file absent
  from the baseline holds any;
- the check also fails when a file holds fewer comments than its baseline, and names the
  command that lowers the baseline, so a deleted comment cannot come back.

Do not build the ratchet from inline suppression comments: they add what the rule bans.
When no comment remains, the plain rule is enough and no baseline is needed.

When a rule from an earlier pass exists, keep it and lower its baseline. Widen its scope
only if this pass covered more code.

Prove the rule works. Add a comment to a file in the scope and confirm the check fails,
then remove the comment and confirm the check passes.

### Measuring

Measure; do not estimate from a sample. Count lines of code as lines in the source files of
the scope, without the files the pass adds, such as the ADRs and the lint rule.

- lines shed by this pass: the line count of the scope before the pass, minus the count
  after it;
- lines still to shed: the lines that deleting every remaining non-functional comment
  would remove, that is the lines that hold only such a comment. The blank lines removed
  with them are not known yet, so this figure is a minimum;
- the total of both, and its share of the scope's lines before the pass.

A comment at the end of a line of code sheds no line; count these comments apart.

## Report

Write the report in the language the user writes in. Keep code identifiers, file paths and
technical terms in their original form.

Start with one line: the scope, the number of comments found, the number deleted and the
number that remain. Then give:

- **classes**: the number of comments in each class;
- **issues**: each issue filed, with its link and the code it concerns, then each issue
  that could not be filed, with its text;
- **ADRs**: each ADR written or completed, with its path and the decision in one line;
- **lint rule**: where it is declared, the command that runs it, the baseline file and the
  count it records, and the result of the proof;
- **lines of code**: the three figures from "Measuring";
- **possible defects**: each comment that contradicts the code, with `file:line`;
- **unsorted**: the comments left in place, grouped by reason when there are many;
- **limits**: the files not sorted in this pass, the languages read without a tokenizer,
  the comments restored for a check, and the project checks that could not run or that
  failed, with their output.
