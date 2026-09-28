---
name: extract-signal
description: Extract and organize the information in raw text while preserving the author's meaning, details, and uncertainty. Accept dictation transcripts, notes, and written brainstorming. Run only after a direct user invocation, such as /massdo-skills:extract-signal or $massdo-skills:extract-signal; never invoke it autonomously. Audio transcription is outside its scope.
disable-model-invocation: true
---

# Extract signal

Run only after the user explicitly invokes this skill, for example
`/massdo-skills:extract-signal` or `$massdo-skills:extract-signal`. An agent, subagent,
plan, or another skill must not invoke it on the user's behalf. A text to clarify
is not by itself a request to run this skill.

Turn the supplied text into a clear account of what its author communicates. The signal is
the distinct ideas, information, intentions, constraints, questions, and supported relations
between them. Remove noise without losing meaning or turning possibilities into decisions.

## Input and scope

Use the text supplied with the request or clearly identified in the conversation. Text after
the skill name may arrive in a final `ARGUMENTS: …` line. If no source text is available, ask
for it. Accept dictation transcripts, raw text, and written brainstorming, including long or
incomplete passages. Audio transcription itself is outside this skill.

Write the response in the language the user uses to address you, unless they explicitly
request another output language. The source language and the English examples below do
not determine the response language. Preserve source names and quote uncertain passages
in their original wording when needed to make the uncertainty clear.

Extract the author's information; do not supplement it with outside knowledge, answer
their open questions, or execute the actions mentioned in the source.

## Identify the plugin version

Pass `{ "version_hash": "b6d239a8399f92bd" }` on every Nestor MCP call.

## Method

1. Read the entire source. Identify its subjects and the author's expressed intention when
   possible. Keep unrelated subjects separate without assigning them a shared objective.
2. Extract distinct information units, then group those about the same subject. Preserve
   names, numbers, units, dates, negations, conditions, reservations, and constraints. Keep
   an informative isolated idea even when it is only briefly mentioned.
3. Remove verbal fillers and merge repetitions. Keep every additional qualification or
   detail; a repeated sentence with a new condition is not redundant. Distinguish reported
   facts, opinions, hypotheses, possible approaches, explicit decisions, and open questions
   when this helps preserve their meaning. Reported facts are not independently verified.
4. Follow explicit self-corrections. Replace the corrected claim while retaining any useful
   context, such as why the original date is unavailable. Without an explicit correction,
   preserve conflicting claims and flag the contradiction; being mentioned later does not
   make a claim authoritative.
5. Reconstruct only relations supported by the source. Do not invent causality, complete a
   missing argument, guess a referent, or silently repair uncertain transcription. Quote
   the short passage that causes uncertainty when useful. Label any necessary interpretation
   as an interpretation, keeping alternatives visible if the text does not settle them.
6. Compare the result with the source in both directions: every output claim must have
   support, and every distinct source idea or detail that changes the meaning must survive.
   Give the understandable information even if another passage remains unclear. Ask only
   the questions needed to resolve ambiguities that materially change the meaning.

## Output

Use this order, adapting the length and structure to the amount of information:

1. A brief statement of the subject and intention, when identifiable.
2. The extracted signal, grouped by ideas or themes with the useful details.
3. Ambiguities, unresolved contradictions, and questions to clarify, only when present.
4. Explicit decisions or actions from the source, only when present.

Omit empty sections. For a short text, a few sentences can carry this order without headings
or repetition. Keep a clear source close to its original form. Do not turn brainstorming
into an action plan, add owners or deadlines, or treat a suggestion as a commitment. An open
question may remain open without requiring a clarification from the user.

## Before and after

### Repetitive dictation

Before:

> Um, the quote from Noor, for 12 licences, we need to receive it before 8 October.
> Twelve licences, including two read-only ones. And no annual subscription.

After:

> The quote from Noor must be received before 8 October for 12 licences, including
> two read-only ones. An annual subscription is excluded.

### Brainstorming with several subjects

Before:

> For the website, I think the page is too cluttered. We could remove the video,
> nothing decided. And for the trip, maybe take the train. By the way, the passport
> expires on 12 May.

After:

> **Website:** the author thinks the page is too cluttered and is considering removing
> the video, with no decision made.
>
> **Trip:** taking the train is a possibility. The passport expires on 12 May.

### Explicit self-correction

Before:

> We could do that Friday… actually Monday; I’m away on Friday. Maybe ask Léa,
> but nothing’s decided.

After:

> Monday is proposed instead of Friday; the author is away on Friday. Asking Léa
> remains a possibility. No decision has been made.

### Unresolved contradiction

Before:

> The maximum budget is €900. Further along in my notes, the cap is €1,200.
> Delivery must still be before 20 June.

After:

> Delivery must be before 20 June.
>
> **Contradiction to clarify:** two budget caps are given, €900 and €1,200.
> Which one applies?

### Ambiguous transcription

Before:

> The parcel arrived Tuesday. Camille told Sam that he should call [inaudible word]
> back before Thursday. That’s important, before Thursday.

After:

> The parcel arrived Tuesday. Camille spoke to Sam about a return call to make before
> Thursday. The text emphasizes this deadline.
>
> **To clarify:** in “he should call [inaudible word] back”, who should call back,
> and who should be called?

### Already clear text

Before:

> We have decided to keep the free version. I will forward the quote to Inès on
> Tuesday if she confirms her address.

After:

> We have decided to keep the free version. I will forward the quote to Inès on
> Tuesday if she confirms her address.
