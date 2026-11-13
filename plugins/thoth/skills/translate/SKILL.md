---
name: translate
description: Fait avancer un flux de traduction de Thoth depuis cette session, à la demande du traducteur expert de traduire, de continuer ou de reprendre un flux.
argument-hint: "[flowId] [<slot>=<tactic>[@<version>][,…]]… | resume <flowId>"
---

Appelle l'outil `thoth_read_procedure` avec `name` : `translate`, puis suis le texte qu'il rend, avec ces arguments : `$ARGUMENTS`

Si cet outil manque, Thoth n'est pas connecté : affiche « Thoth n'est pas connecté : tapez /mcp, choisissez thoth, puis Authenticate, et relancez la commande. » et arrête-toi. S'il refuse ou ne répond pas, affiche son code et son message, et arrête-toi.

Si ce texte n'est plus dans ton contexte, rappelle l'outil avant de continuer.
