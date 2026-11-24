# Plugin Thoth pour Claude Code

Le plugin relie Claude Code au serveur Thoth de l'agence. La session pilote du traducteur expert conduit un flux par les outils MCP de Thoth ; les hooks du plugin ajoutent à chaque appel l'identité de la session et l'empreinte du plugin et l'autorisent, restreignent les outils des agents de lot à ceux de l'étape et remontent la consommation de jetons.

## Prérequis

- Claude Code, dans un terminal ou dans l'onglet Code de l'app Claude.
- Node 22 au moins : les hooks sont des scripts Node. Chaque hook prend d'abord le Node que `/setup` pose dans `~/.local/share/thoth/node/bin/node`, sinon celui du PATH. Avec une version plus ancienne, le plugin le signale au démarrage de la session et ses hooks restent inactifs.

Un Mac qui n'a que l'app Claude n'a ni la commande `claude`, ni Node, ni Git : l'app garde son Claude Code hors du PATH, et sans les outils de développement d'Apple, `git` n'ouvre que la fenêtre qui propose de les installer. L'installation se passe des trois ([ADR 0043](../docs/adr/0043-plugin-installs-without-developer-tools.md)).

## Installation

Le plugin est publié dans la marketplace publique de l'agence, `massdo-marketplace` (dépôt GitHub `massdo/massdo-marketplace`). Son catalogue servi en HTTPS, `.claude-plugin/marketplace-http.json`, donne Thoth en archive ZIP, que Claude Code installe sans Git ; le catalogue du dépôt reste valable pour un poste qui a Git. L'installation tient en trois gestes :

1. Ouvrir `<adresse>/install`, page publique où renvoie aussi la page de connexion ; une fois connecté, Installation et la page Flux, tant qu'aucun flux n'existe, la donnent aussi. La section « Installer Thoth dans Claude Code » y donne le prompt d'installation et son bouton Copier : il demande d'installer le plugin, d'activer sa mise à jour automatique et, si Node 22 manque, de télécharger le Node officiel, puis de lancer `curl -fsSL <adresse>/setup` et de suivre les instructions affichées.
2. Coller ce prompt dans Claude Code, qui lit `/setup` par curl, tel quel, sans ouvrir de navigateur. La page `/setup`, publique et sans secret, lui fait lancer Claude Code par `"${CLAUDE_CODE_EXECPATH:-claude}"`, le Claude Code de l'app hors du PATH, sinon la commande `claude` ; poser Node 22 si besoin, téléchargé de nodejs.org et vérifié par son empreinte, sans mot de passe ; ajouter ou mettre à jour `massdo-marketplace` par son catalogue HTTPS ; activer sa mise à jour automatique ; installer `thoth@massdo-marketplace` et poser son adresse par `plugin configure thoth@massdo-marketplace --values-stdin`.
3. Se connecter dans le navigateur : `/setup` fait lancer `mcp login plugin:thoth:thoth`, comme décrit ci-dessous, puis une nouvelle session Claude Code donne `/thoth:translate`.

## Connexion au serveur

Le plugin a une seule option : `server_url`, l'adresse du serveur Thoth, sans barre finale, par exemple `https://thoth.example.org`, que `/setup` pose à l'installation. Il se connecte au serveur par OAuth, sans jeton à copier ([ADR 0039](../docs/adr/0039-plugin-connects-through-oauth.md)) :

1. `claude mcp login plugin:thoth:thoth`, que `/setup` fait lancer à Claude (sur macOS dans `script`, qui lui donne un terminal) ; à défaut, dans une session Claude Code, `/mcp`, choisir `thoth` puis « Authenticate ».
2. Le navigateur s'ouvre sur Thoth : se connecter avec le compte du traducteur expert, puis cliquer « Autoriser ». Claude ne demande jamais de mot de passe dans le chat.
3. `claude mcp list` montre `plugin:thoth:thoth` connecté. Claude Code garde l'accès pour lui ; Claude ne le voit jamais.

La page Installation, dans l'interface de Thoth, liste les connexions de Claude Code et révoque celle d'un poste : son accès est coupé aussitôt, et `/mcp` demande de s'authentifier de nouveau. Les hooks n'emploient pas cet accès : ils appellent Thoth sous l'identifiant de leur session Claude Code, que Thoth reconnaît tant qu'elle a fait un appel MCP depuis moins de 7 jours ([ADR 0038](../docs/adr/0038-plugin-hooks-authenticate-by-session.md)).

Depuis la version 2.0.0 du plugin (12 novembre 2026), il se connecte par OAuth, sans jeton ni option `token`, ses hooks s'authentifient par leur session Claude Code, et le skill `replay`, outil de développement, n'est plus dans la version publiée : il reste dans le dépôt et dans la marketplace locale `thoth-dev`. Les skills et l'agent de lot lisent leur procédure sur le serveur après la connexion : le plugin n'en garde que le nom.

Depuis la version 2.1.0 du plugin (15 novembre 2026), `/thoth:resume <flowId>` reprend un flux déjà démarré dans le mode de son lancement ; il lit la procédure de `translate` avec `resume <flowId>`.

Depuis la version 2.2.0 du plugin, l'agent de lot peut appeler `thoth_read_style_rules` et `thoth_search_style_rules` pour lire et chercher les règles de style du flux : son instruction de style, puis le guide de style de l'organisation et la Bible qu'il a retenus.

Depuis la version 2.0.1 (14 novembre 2026), le hook qui ajoute l'identité autorise lui-même chaque appel à Thoth : en mode de permission auto, Claude Code refusait ces appels, parce que le hook les modifie. Les outils de Thoth ne demandent donc plus de confirmation, dans aucun mode ; les règles de refus des réglages de Claude Code s'appliquent toujours. Avec la version 2.0.0, une session en mode de permission auto ne joint plus Thoth : lancer `claude plugin marketplace update massdo-marketplace`, puis `claude plugin update thoth@massdo-marketplace`, et ouvrir une nouvelle session.

Aucune variable d'environnement n'est à définir sur le poste. Pour changer d'adresse, lancer `/plugin configure thoth@massdo-marketplace`, puis ouvrir une nouvelle session. Sans adresse, le serveur MCP ne se connecte pas et les hooks n'envoient rien : les relevés de consommation attendent sur le poste.

## Mise à jour du plugin

La mise à jour automatique de `massdo-marketplace`, désactivée par défaut pour une marketplace tierce, est activée par `/setup` : `"autoUpdate": true` sur l'entrée `massdo-marketplace` de `extraKnownMarketplaces`, dans `~/.claude/settings.json`. Sur un poste installé avant, relancer `/setup` ou l'activer dans Claude Code : `/plugin` → Marketplaces → `massdo-marketplace` → Enable auto-update. Claude Code met alors le plugin à jour en arrière-plan après le début d'une session, et la nouvelle version se charge à la session suivante ; une session en cours garde la sienne. Chaque publication doit monter la version du plugin : Claude Code ne remplace pas une copie de même version.

Quand une version plus récente existe, le serveur le signale une fois dans la session, qui continue. Quand il refuse le plugin, périmé pour le template du flux ou inconnu, la session lance `"${CLAUDE_CODE_EXECPATH:-claude}" plugin update thoth@massdo-marketplace`, s'arrête et donne la commande à taper dans une nouvelle session, `/thoth:resume <flowId>` pour un flux démarré : l'empreinte du plugin s'écrit au démarrage de la session, et seule une nouvelle session envoie celle de la nouvelle version. Cette consigne vient du serveur, dans le champ `action` de l'avis et du refus : elle change sans republier le plugin ([ADR 0035](../docs/adr/0035-plugin-update-instruction-from-server.md)). L'empreinte ne compte pas les marqueurs que Claude Code écrit à la racine du dossier installé.
