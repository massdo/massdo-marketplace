# Plugin Thoth pour Claude Code

Le plugin relie Claude Code au serveur Thoth de l'agence. La session pilote du traducteur expert conduit un flux par les outils MCP de Thoth ; les hooks du plugin ajoutent à chaque appel l'identité de la session et l'empreinte du plugin, restreignent les outils des agents de lot à ceux de l'étape et remontent la consommation de jetons.

## Prérequis

- Claude Code.
- Node 22 au moins : les hooks sont des scripts Node. Avec une version plus ancienne, le plugin le signale au démarrage de la session et ses hooks restent inactifs.

## Installation

Le plugin est publié dans la marketplace publique de l'agence, `massdo-marketplace` (dépôt GitHub `massdo/massdo-marketplace`) : `claude plugin install thoth@massdo-marketplace`. L'installation tient en trois gestes :

1. Se connecter à Thoth et ouvrir Réglages : la section « Installer Thoth dans Claude Code » donne le prompt « Va sur <adresse>/setup et suis les instructions. » et son bouton Copier.
2. Coller ce prompt dans Claude Code. La page `/setup`, publique et sans secret, lui donne les commandes : vérifier Node 22 et `claude`, passer les clones en HTTPS (`CLAUDE_CODE_PLUGIN_PREFER_HTTPS`) sans clé SSH GitHub, ajouter ou mettre à jour `massdo-marketplace`, installer `thoth@massdo-marketplace` et poser son adresse par `claude plugin configure thoth@massdo-marketplace --values-stdin`.
3. Dans une nouvelle session Claude Code, s'authentifier par `/mcp` comme décrit ci-dessous.

## Connexion au serveur

Le plugin a une seule option : `server_url`, l'adresse du serveur Thoth, sans barre finale, par exemple `https://thoth.example.org`, que `/setup` pose à l'installation. Il se connecte au serveur par OAuth, sans jeton à copier ([ADR 0039](../docs/adr/0039-plugin-connects-through-oauth.md)) :

1. Dans une nouvelle session Claude Code, taper `/mcp`, choisir `thoth` puis « Authenticate ».
2. Le navigateur s'ouvre sur Thoth : se connecter avec le compte du traducteur expert, puis cliquer « Autoriser ». Claude ne demande jamais de mot de passe dans le chat.
3. De retour dans Claude Code, `/mcp` montre `thoth` connecté. Claude Code garde l'accès pour lui ; Claude ne le voit jamais.

Réglages, dans l'interface de Thoth, liste les connexions de Claude Code et révoque celle d'un poste : son accès est coupé aussitôt, et `/mcp` demande de s'authentifier de nouveau. Les hooks n'emploient pas cet accès : ils appellent Thoth sous l'identifiant de leur session Claude Code, que Thoth reconnaît tant qu'elle a fait un appel MCP depuis moins de 7 jours ([ADR 0038](../docs/adr/0038-plugin-hooks-authenticate-by-session.md)).

Depuis la version 2.0.0 du plugin (12 novembre 2026), il se connecte par OAuth, sans jeton ni option `token`, ses hooks s'authentifient par leur session Claude Code, et le skill `replay`, outil de développement, n'est plus dans la version publiée : il reste dans le dépôt et dans la marketplace locale `thoth-dev`. Les skills et l'agent de lot lisent leur procédure sur le serveur après la connexion : le plugin n'en garde que le nom.

Aucune variable d'environnement n'est à définir sur le poste. Pour changer d'adresse, lancer `/plugin configure thoth@massdo-marketplace`, puis ouvrir une nouvelle session. Sans adresse, le serveur MCP ne se connecte pas et les hooks n'envoient rien : les relevés de consommation attendent sur le poste.

## Mise à jour du plugin

Activer une fois la mise à jour automatique de `massdo-marketplace`, désactivée par défaut pour une marketplace tierce : dans Claude Code, `/plugin` → Marketplaces → `massdo-marketplace` → Enable auto-update. Une nouvelle version se charge alors à la session suivante ; une session en cours garde la sienne.

Quand une version plus récente existe, le serveur le signale une fois dans la session, qui continue. Quand il refuse le plugin, périmé pour le template du flux ou inconnu, la session lance `claude plugin update thoth@massdo-marketplace`, s'arrête et donne la commande à taper dans une nouvelle session, `/thoth:translate resume <flowId>` pour un flux démarré : l'empreinte du plugin s'écrit au démarrage de la session, et seule une nouvelle session envoie celle de la nouvelle version. Cette consigne vient du serveur, dans le champ `action` de l'avis et du refus : elle change sans republier le plugin ([ADR 0035](../docs/adr/0035-plugin-update-instruction-from-server.md)). L'empreinte ne compte pas les marqueurs que Claude Code écrit à la racine du dossier installé.
