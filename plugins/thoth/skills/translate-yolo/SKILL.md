---
name: translate-yolo
description: Lance en mode YOLO un flux de Thoth pas encore démarré, seulement sur la commande /thoth:translate-yolo tapée par le traducteur expert.
argument-hint: "[flowId] [<slot>=<tactic>[@<version>][,…]]… [<yolo-tactic>[@<version>]]"
disable-model-invocation: true
---

Appelle l'outil `thoth_read_procedure` avec `name` : `translate-yolo`, puis suis le texte qu'il rend, avec ces arguments : `$ARGUMENTS`

Si cet outil manque, Thoth n'est pas connecté : affiche « Thoth n'est pas connecté : tapez /mcp, choisissez thoth, puis Authenticate, et relancez la commande. » et arrête-toi. S'il refuse ou ne répond pas, affiche son code et son message, et arrête-toi.

Si ce texte n'est plus dans ton contexte, rappelle l'outil avant de continuer.
