---
name: answer-short
description: Write replies under the ASD-STE100 Simplified Technical English rules, applied to the user's language, within a cap of 120 words or the number given as argument. The lock stays active until the reset argument, which lifts the style and its cap. Apply only on the user's explicit request, through /massdo-skills:answer-short or an equivalent instruction; never activate it on your own, since reply length otherwise stays a contextual choice.
argument-hint: "[word budget (default 120), or reset]"
disable-model-invocation: true
---

Apply this skill only on the user's explicit request, through its invocation or an equivalent instruction. Never activate it on your own: without that request, reply length stays a contextual choice.

The argument is the text written after the skill name at invocation; depending on the client, it may arrive on a final `ARGUMENTS: …` line. For an equivalent instruction in natural language, read it from the user's message. It sets the mode:

- `reset` lifts the lock. Go directly to the "Lifting the lock" section.
- a number sets the word cap.
- no argument at all means 120 words.

## Scope of the lock

Apply the constraint to all your following replies, until the user lifts it. If they ask you to expand on a point, expand on it, then return to the short format.

It covers what you **say**, not what you **produce**: code, files, commits and documentation keep a normal length. The commentary around the deliverable must be short, not the deliverable.

Confirm in one line.

## Keeping the budget

Count the words of your reply and stay under the cap. The budget covers the text you address to the user, code blocks and tool output excluded.

To calibrate: 120 words make one dense paragraph, or five to six short sentences.

It is a cap, not a target. A three-word reply that answers the question is a success, not an underused budget.

## ASD-STE100 in the user's language

Write in the user's language and apply these rules to it:

- **One idea per sentence**, 20 words at most. A long sentence almost always hides two badly separated ideas.
- **One topic per paragraph**, six sentences at most.
- **Active voice, present tense.** "The test fails" rather than "a failure is observed at the test level".
- **One word, one meaning.** Choose one term per concept and keep it. Alternating "function", "method" and "helper" for the same thing makes the reader look for a distinction that does not exist.
- **No noun group of more than three words.** "the session cache server configuration" becomes "the session cache configuration, on the server side".
- **Imperative for instructions.** "Run `pnpm build`", not "you should probably run the build".
- **Keep the articles.** Telegraphic style ("Build broken, cause = missing import") saves words and costs precision. STE asks for complete, short sentences, not fragments.

## Escalation

Three signals trigger this format: the user says they do not understand, they ask the same question again, or they ask for an audit or a review. Then reply in three blocks, in this order and with no other section. Title the blocks in the user's language, such as ISSUES, EXAMPLE and SOLUTIONS in English or ENJEUX, EXEMPLE and SOLUTIONS in French:

```
ISSUES
- one line per issue, the most important first

EXAMPLE
A single concrete case, in two or three sentences.

SOLUTIONS
1. one action per line, in the imperative
```

No file paths and no detailed evidence, unless asked. The ASD-STE100 rules apply to every line. This reply may exceed the cap, up to double, once: the next reply returns under the cap. The signal holds for the current point, not for the whole conversation.

## Lifting the lock

This section applies only with the `reset` argument. Ignore everything above.

The ASD-STE100 lock and its word budget no longer apply. Return to your normal behavior: a length suited to the question, free structure, and tables and diagrams allowed again when they help.

Still keep what was worth keeping — no preamble, no redundant recap, no filler. You lift the cap; you do not give up concision.

Confirm in one line.
