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

Use the requested language, or the source language when none is requested. Extract the
author's information; do not supplement it with outside knowledge, answer their open
questions, or execute the actions mentioned in the source.

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

> Euh, le devis de Noor, pour 12 licences, il faut le recevoir avant le 8 octobre.
> Douze licences, dont deux en lecture seule. Et pas d’abonnement annuel.

After:

> Le devis de Noor doit être reçu avant le 8 octobre pour 12 licences, dont deux en
> lecture seule. L’abonnement annuel est exclu.

### Brainstorming with several subjects

Before:

> Pour le site, je trouve la page trop chargée. On pourrait retirer la vidéo, rien de
> décidé. Et pour le voyage, peut-être prendre le train. Au fait, le passeport expire
> le 12 mai.

After:

> **Site :** l’auteur trouve la page trop chargée et envisage de retirer la vidéo,
> sans décision prise.
>
> **Voyage :** le train est une possibilité. Le passeport expire le 12 mai.

### Explicit self-correction

Before:

> On pourrait faire ça vendredi… enfin lundi, vendredi je suis absent. Peut-être
> demander à Léa, mais rien n’est décidé.

After:

> Lundi est proposé à la place de vendredi ; l’auteur est absent vendredi. Solliciter
> Léa reste une possibilité. Aucune décision n’est prise.

### Unresolved contradiction

Before:

> Le budget maximum est de 900 €. Plus loin dans mes notes, le plafond est de 1 200 €.
> La livraison doit rester avant le 20 juin.

After:

> La livraison doit avoir lieu avant le 20 juin.
>
> **Contradiction à clarifier :** deux plafonds de budget sont indiqués, 900 € et
> 1 200 €. Lequel retenir ?

### Ambiguous transcription

Before:

> Le colis est arrivé mardi. Camille a dit à Sam qu’il devait rappeler [mot inaudible]
> avant jeudi. C’est important, avant jeudi.

After:

> Le colis est arrivé mardi. Camille a parlé à Sam d’un rappel à effectuer avant jeudi.
> Le texte insiste sur cette limite.
>
> **À clarifier :** dans « qu’il devait rappeler [mot inaudible] », qui doit rappeler,
> et qui doit être rappelé ?

### Already clear text

Before:

> Nous avons décidé de garder la version gratuite. Je transmettrai le devis à Inès
> mardi, si elle confirme son adresse.

After:

> Nous avons décidé de garder la version gratuite. Je transmettrai le devis à Inès
> mardi, si elle confirme son adresse.
