---
name: resume
description: Reprend dans cette session un flux de Thoth déjà démarré, dans le mode de son lancement, seulement sur la commande /thoth:resume tapée par le traducteur expert.
argument-hint: "<flowId>"
disable-model-invocation: true
---

Appelle l'outil `thoth_read_procedure` avec `name` : `translate`, puis suis le texte qu'il rend, avec ces arguments : `resume $ARGUMENTS`

Si cet outil manque, Thoth n'est pas connecté : affiche « Thoth n'est pas connecté : tapez /mcp, choisissez thoth, puis Authenticate, et relancez la commande. » et arrête-toi. S'il refuse ou ne répond pas, affiche son code et son message, et arrête-toi.

Si ce texte n'est plus dans ton contexte, rappelle l'outil avant de continuer.
