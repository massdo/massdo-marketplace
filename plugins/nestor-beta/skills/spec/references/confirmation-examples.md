# Confirmation examples

These exchanges illustrate the expected tone; they are not runtime evidence. Conduct the
real exchange in the user's language, with the actual slugs and server results. `A` is
the agent and `U` the user.

## Normal wording

Every question fits in one sentence and names the decision only. None of them repeats
this skill's path, quotes its rules or explains save, approval and inspection again.

Not this, before every question:

> The Spec skill (`…/skills/spec/SKILL.md`) requires: "Ask for confirmation before any
> write." This confirmation authorises the save; approval and inspection stay distinct.

A higher-priority client instruction may still require naming or linking the skill when
it causes a confirmation or a pause. Follow it in its shortest accepted form, next to the
question, without quoting rules around it. This skill cannot remove that obligation.

## End of interview

> A: I have everything I need. Shall I compile the complete work?
> U: Yes.

The agent shows the specification, the tree with each node's kind, the dependencies and
the fields being replaced.

## Save

> A: Save it to Nestor?
> U: Yes.

The agent writes, then reports the saved slugs. This yes authorises the save only.

> U, after reading the compiled work: Looks good, save it.

The agent saves without asking again. When reconciliation or a user request changes that
content before the write, it asks again.

## Approval

> A: Saved as `brown_turtle`. Approve it for build?
> U: Not yet.
> A: Saved, not approved: it is not ready to build.

> A: Saved as `brown_turtle`. Approve it for build?
> U: Yes.

The agent approves, then inspects. It announces "ready to build" only after inspect
accepts; otherwise it reports the blocking item or prerequisite the server names.

> U, after reading the compiled work: Save and approve it.

The agent saves, approves and inspects without another question.

## Refusal

> A: Save it to Nestor?
> U: No, I want to rework the steps.

No mutation follows. The agent continues the interview on the steps.

When the server refuses an approval, the detailed diagnostic is the useful answer:

> A: Approval refused: `copper_manatee` has a step without verification. Shall I add
> `pnpm test -- csv-export` as its verification?

## Concurrent conflict

A save returns `CONFLICT` with `details.current`. The agent reconciles that state and
retries once with its fresh pair, without replaying the stale change. When the
intervening edit changes the reviewed content, the agent shows it first:

> A: Someone changed the title of `gray_xerinae` meanwhile. Keep their title and save
> the rest?
> U: Yes.

A second refusal stops the save; the agent reports the confirmed ids and the exact
unfinished node.
