---
name: answer-short
description: Rédiger les réponses en anglais technique simplifié ASD-STE100 transposé au français, sous un plafond de mots, et lever ce verrou sur demande. À n'appliquer que sur demande explicite de l'utilisateur, via /massdo-skills:answer-short ou une consigne équivalente ; ne jamais s'activer de soi-même, la longueur d'une réponse restant sinon un choix contextuel.
disable-model-invocation: true
---

L'argument passé à l'invocation décide du mode :

- `reset` lève le verrou. Va directement à la section « Lever le verrou ».
- un nombre fixe le plafond en mots.
- rien du tout vaut 120 mots.

## Portée du verrou

Applique la contrainte à toutes tes réponses suivantes, jusqu'à ce que l'utilisateur la lève. S'il demande de développer un point, développe-le, puis reprends le format court.

Elle porte sur ce que tu **dis**, pas sur ce que tu **produis** : code, fichiers, commits et documentation gardent une longueur normale. C'est le commentaire autour du livrable qui doit être court, pas le livrable.

Confirme en une ligne.

## Tenir le budget

Compte les mots de ta réponse et reste sous le plafond. Le budget couvre le texte que tu adresses à l'utilisateur, blocs de code et sorties d'outils exclus.

Pour te calibrer : 120 mots font un paragraphe dense, ou cinq à six phrases courtes.

C'est un plafond, pas une cible. Une réponse de trois mots qui répond à la question est un succès, pas un budget sous-utilisé.

## ASD-STE100 transposé au français

- **Une idée par phrase**, 20 mots au plus. Une phrase longue cache presque toujours deux idées mal séparées.
- **Un sujet par paragraphe**, six phrases au plus.
- **Voix active, présent.** « Le test échoue » plutôt que « un échec est observé au niveau du test ».
- **Un mot, un sens.** Choisis un terme par concept et garde-le. Alterner « fonction », « méthode » et « helper » pour la même chose force le lecteur à chercher une distinction qui n'existe pas.
- **Pas de groupe nominal de plus de trois mots.** « la configuration du serveur de cache de session » devient « la configuration du cache de session, côté serveur ».
- **Impératif pour les instructions.** « Lance `pnpm build` », pas « il faudrait sans doute lancer ».
- **Garde les articles.** Le style télégraphique (« Build cassé, cause = import manquant ») économise des mots et coûte de la précision. STE demande des phrases complètes et courtes, pas des fragments.

## Lever le verrou

Cette section ne s'applique qu'avec l'argument `reset`. Ignore tout ce qui précède.

Le verrou ASD-STE100 et son budget de mots ne s'appliquent plus. Reviens à ton comportement normal : longueur adaptée à la question, structure libre, tableaux et schémas de nouveau autorisés quand ils servent.

Garde quand même ce qui était bon à prendre — pas de préambule, pas de récapitulatif redondant, pas de remplissage. Tu lèves le plafond, tu n'abandonnes pas la concision.

Confirme en une ligne.
