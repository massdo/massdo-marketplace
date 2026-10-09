# Massdo marketplace

Trois plugins : `nestor`, `nestor-beta`, `massdo-skills`. Un seul serveur MCP, livré par `nestor`.

`nestor-beta` s’installe en plus de `nestor`.

## Installer

### Claude Code

```bash
claude plugin marketplace add massdo/massdo-marketplace
claude plugin install nestor@massdo-marketplace
claude plugin install nestor-beta@massdo-marketplace
claude plugin install massdo-skills@massdo-marketplace
```

### Codex

```bash
codex plugin marketplace add massdo/massdo-marketplace
codex plugin add nestor@massdo-marketplace
codex plugin add nestor-beta@massdo-marketplace
codex plugin add massdo-skills@massdo-marketplace
```

### Cursor

```bash
git clone https://github.com/massdo/massdo-marketplace.git "$HOME/massdo-marketplace"
mkdir -p "$HOME/.cursor/plugins/local"
ln -sfn "$HOME/massdo-marketplace/plugins/nestor" "$HOME/.cursor/plugins/local/nestor"
ln -sfn "$HOME/massdo-marketplace/plugins/nestor-beta" "$HOME/.cursor/plugins/local/nestor-beta"
ln -sfn "$HOME/massdo-marketplace/plugins/massdo-skills" "$HOME/.cursor/plugins/local/massdo-skills"
```

Puis **Developer: Reload Window**.

### Kimi Code

```bash
git clone https://github.com/massdo/massdo-marketplace.git "$HOME/massdo-marketplace"
```

Dans le TUI :

```
/plugins install ~/massdo-marketplace/plugins/nestor
/plugins install ~/massdo-marketplace/plugins/nestor-beta
/plugins install ~/massdo-marketplace/plugins/massdo-skills
/reload
```

## MCP

| | Serveur | URL |
|---|---|---|
| 📓 | nestor | `https://journal.mcp-marketplace.org/mcp` |

Branché par le plugin `nestor`. `nestor-beta` et `massdo-skills` n’en déclarent pas.

## Skills

Même skill, quatre écritures :

| Claude Code | Codex | Cursor | Kimi Code |
|---|---|---|---|
| `/nestor:tree` | `$nestor:tree` | `/tree` | `/skill:tree` |

Les commandes ci-dessous sont la forme Claude Code.

### 📓 nestor

```
/nestor:nestor
/nestor:activity
/nestor:tree
/nestor:check-for-updates
```

| | Skill | |
|---|---|---|
| 📓 | `nestor` | Tâches, notes, projets, historique |
| ⏱️ | `activity` | Chrono et rapports de temps |
| 🌳 | `tree` | Arbre ASCII du projet |
| 🔄 | `check-for-updates` | Version installée de nestor |

### 🧪 nestor-beta

```
/nestor-beta:nestor-beta
/nestor-beta:build
/nestor-beta:ship
/nestor-beta:ship list
/nestor-beta:doctor
/nestor-beta:clean-task
/nestor-beta:next-tasks
/nestor-beta:spec
/nestor-beta:check-for-updates
```

| | Skill | |
|---|---|---|
| 🔗 | `nestor-beta` | Footer `nestor tasks:` sur les pull requests |
| 🏗️ | `build` | Une tâche vers une pull request |
| 🚢 | `ship` | PR ouvertes, puis merge dans `main` |
| 🩺 | `doctor` | Tâches livrées à clôturer |
| 🧹 | `clean-task` | Nettoyer le corps d’une tâche |
| 📋 | `next-tasks` | Tâches actives d’un projet |
| 📐 | `spec` | Une idée vers un arbre de tâches |
| 🔄 | `check-for-updates` | Version installée de nestor-beta |

`ship list` ne fait que lister.

### ✨ massdo-skills

```
/massdo-skills:answer-short
/massdo-skills:articulate
/massdo-skills:chief-of-staff
/massdo-skills:extract-signal
/massdo-skills:extract-signal raw
```

| | Skill | |
|---|---|---|
| ✂️ | `answer-short` | Réponses courtes. `reset` lève le style |
| ✍️ | `articulate` | Phrases complètes. `reset` lève le style |
| 🎯 | `chief-of-staff` | Décider, mener par le résultat. `reset` lève la posture |
| 📡 | `extract-signal` | Clarifier un texte brut. `raw` renvoie le signal seul |
