<p align="center">
  <img src=".github/assets/hero.svg" width="100%" alt="massdo marketplace: Nestor, the wise old king with a laurel wreath, a staff and a scroll, inside a ring of neon lights over a synthwave grid. nestor is for everyone, nestor-beta is for coders.">
</p>

<p align="center">
  <b>Your tasks, notes and projects, with Nestor.</b><br>
  Set it up once, then ask for what you need in your own words.
</p>

<br>

## 🏛️ Three plugins

<p align="center">
  <img src=".github/assets/menu.svg" width="100%" alt="nestor is for everyone: tasks, notes, projects and hours, no code needed. nestor-beta is for coders: from an idea to tasks, pull requests and merges. massdo-skills is for style: it changes how your agent talks to you and works on its own.">
</p>

Start with **nestor** to manage your tasks, notes and projects. No coding needed.
**nestor-beta** adds coding tools. **massdo-skills** changes how your assistant responds.
Both are optional.

## 🕹️ Install

You will copy a setup command, connect your account in your browser, then start a conversation.

**Before you start:** install and sign in to
[Codex for the terminal](https://learn.chatgpt.com/docs/codex/cli) or
[Claude Code](https://code.claude.com/docs/en/quickstart). On Mac or Linux,
[Cursor Agent](https://docs.cursor.com/en/cli/installation) is also supported.
If you use [Grok Bot](https://docs.x.ai/grok-bot/overview), setup shows the
steps to connect Nestor in your Grok account.
For Codex, Claude Code and Cursor Agent, you also need
[Git](https://git-scm.com/install/) to download Nestor.

### 1. Copy the setup command

Choose your computer below. Copy the whole block into the window described, then press **Enter**.
Use the Terminal or PowerShell window for this step.
You will open your conversation in step 3.

<details>
<summary><b>Mac or Linux</b></summary>

On a Mac, press **⌘ Space**, type **Terminal**, then press **Enter**.
On Linux, open **Terminal** from your applications.

```bash
curl -fsSL https://raw.githubusercontent.com/massdo/massdo-marketplace/main/install.sh | bash
```

</details>

<details>
<summary><b>Windows</b></summary>

Open **Start**, search for **PowerShell**, then open it.

```powershell
$installerPath = Join-Path ([IO.Path]::GetTempPath()) ('nestor-' + [guid]::NewGuid() + '.ps1')
try {
    Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/massdo/massdo-marketplace/main/install.ps1' -OutFile $installerPath
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath
} finally {
    Remove-Item -LiteralPath $installerPath -ErrorAction SilentlyContinue
}
```

Some Windows installations are not supported yet. If setup says it cannot use your app,
[ask for help](https://github.com/massdo/massdo-marketplace/issues/new).

<details>
<summary>Windows compatibility details</summary>

The installer requires `codex.exe` or `claude.exe` on `PATH`.
It rejects `.cmd`, `.bat` and `.ps1` launchers, including the npm shims
`codex.cmd` and `claude.cmd`. It supports Windows PowerShell 5.1+ and PowerShell 7.

</details>

</details>

If you use Linux through WSL on Windows, use the **Mac or Linux** command in your WSL terminal.

### 2. Connect Nestor

On Mac or Linux, setup lists the apps found on your computer and marks the ones
that already have Nestor. Move with the arrow keys, press **x** to select or clear
an app, then press **Enter**. Windows setup asks you to type `codex` or `claude` instead.
If it asks to open your browser, press **y**.
Follow the instructions in your browser to sign in and allow the connection.
Then return to the terminal window.

If you already connected Nestor, setup may finish without opening your browser.

### 3. Start a new conversation

When you see **`Installation complete`**, Nestor is ready.
For Cursor, reload the app or start a new Agent session if the new plugin is not
visible yet. Grok Bot setup remains pending until you add Nestor as a custom
connector on [grok.com/connectors](https://grok.com/connectors) and sign in.
Open a **new conversation** in the app you chose, then type:

```text
Show my tasks.
```

**Setup did not finish?** If you see **`Nestor is installed — finish connecting your account`**,
follow the message shown. You can paste the same setup command again to continue.
If your internet connection stopped, reconnect before trying again.

For any other error, [ask for help](https://github.com/massdo/massdo-marketplace/issues/new).
Tell us whether you use Mac, Windows or Linux, and which app you chose.

### Remove Nestor

On Mac or Linux, run the removal wizard:

```bash
curl -fsSL https://raw.githubusercontent.com/massdo/massdo-marketplace/main/uninstall.sh | bash
```

It lists the apps found on your computer, preselects the ones that have Nestor,
and removes it from the apps you confirm. For Grok Bot it shows the steps on
grok.com, because its connectors live in your Grok account. The shared
marketplace stays available for any other plugins you use.

### Manual installation

<details>
<summary>Other ways to install, including the optional plugins</summary>

The commands below are an alternative to the setup above. They include all three plugins.
For Nestor alone, use the marketplace command and the Nestor install command for your app.
Connection and recovery instructions are in the [setup reference](docs/installation.md).

<details>
<summary><b>Claude Code</b></summary>

```bash
claude plugin marketplace add massdo/massdo-marketplace
claude plugin install nestor@massdo-marketplace
claude plugin install nestor-beta@massdo-marketplace
claude plugin install massdo-skills@massdo-marketplace
```

</details>

<details>
<summary><b>Codex</b></summary>

```bash
codex plugin marketplace add massdo/massdo-marketplace
codex plugin add nestor@massdo-marketplace
codex plugin add nestor-beta@massdo-marketplace
codex plugin add massdo-skills@massdo-marketplace
```

</details>

<details>
<summary><b>Cursor</b></summary>

```bash
git clone https://github.com/massdo/massdo-marketplace.git "$HOME/massdo-marketplace"
mkdir -p "$HOME/.cursor/plugins/local"
cp -R "$HOME/massdo-marketplace/plugins/nestor" "$HOME/.cursor/plugins/local/nestor"
cp -R "$HOME/massdo-marketplace/plugins/nestor-beta" "$HOME/.cursor/plugins/local/nestor-beta"
cp -R "$HOME/massdo-marketplace/plugins/massdo-skills" "$HOME/.cursor/plugins/local/massdo-skills"
```

Then run **Developer: Reload Window**.

</details>

<details>
<summary><b>Kimi Code</b></summary>

```bash
git clone https://github.com/massdo/massdo-marketplace.git "$HOME/massdo-marketplace"
```

Then, in the TUI:

```text
/plugins install ~/massdo-marketplace/plugins/nestor
/plugins install ~/massdo-marketplace/plugins/nestor-beta
/plugins install ~/massdo-marketplace/plugins/massdo-skills
/reload
```

</details>

</details>

## 🪄 Use

Tell Nestor what you need in your conversation with Codex or Claude Code. For example:

```text
Show my tasks.
Add "Call the dentist" to my tasks.
Find my notes about Lisbon.
```

<details>
<summary>Optional: commands and shortcuts</summary>

You can also use a command for a specific action:

```text
Claude Code   /nestor:tree
Codex         $nestor:tree
Cursor        /tree
Kimi Code     /skill:tree
```

The command lists below use the Claude Code format.

</details>

### 📜 nestor · for everyone

Like the old king of Pylos, it remembers everything. Tasks, notes, projects and hours, in plain words. No code needed: mention a task and it shows up on its own.

<p align="center">
  <img src=".github/assets/nestor-cloud.svg" width="100%" alt="One memory for all your AI agents: Claude Code, Codex, Cursor and Kimi Code are wired to the Nestor cloud. Claude Code adds book hotel, Cursor asks what is next, Codex marks it done, Kimi Code finds the Lisbon notes.">
</p>

A trip, a building site, a client project, a family move: your tasks live in the cloud, not in one agent. Add “book hotel” in Claude Code, Cursor tells you it is next, Codex ticks it off, Kimi Code finds your Lisbon notes.

<p align="center">
  <img src=".github/assets/nestor-search.svg" width="100%" alt="Story: planning a trip to Lisbon. First, semantic search: where did I want to eat? finds dinner spots in Alfama, a table at Ramiro and a pastry list, with no word in common. Then deterministic search: the tag @@lisbon with the todo filter lists every task tagged lisbon, the same list every time.">
</p>

Two ways to find them. **Semantic** search understands what you mean, even with other words. **Deterministic** search sticks to exact words, tags and filters, like the tags in Apple Notes, and gives the same list every time. Ask in plain words and nestor mixes both.

<details>
<summary>Show Nestor shortcuts and advanced options</summary>

- 📓 `/nestor:nestor` — tasks, notes, projects, history
- ⏱️ `/nestor:activity` — start a timer, get your hours
- 🌳 `/nestor:tree` — draws a project as a tree
- ⏸️ `/nestor:pause` — saves this chat's work context for later
- ▶️ `/nestor:resume` — restores this chat's context without changing it
- 📋 `/nestor:resume list` — lists saved transmissions, newest first, for explicit selection
- 🔖 `/nestor:resume <slug>` — restores that transmission directly
- 🔄 `/nestor:check-for-updates` — looks for an update

Invoke `pause` and `resume` without a project argument: transmissions belong to a chat, not to a project. Pause saves only this chat's work and replaces its previous transmission; text after `pause` tells it what to emphasize. Resume restores this chat's transmission, or the one whose slug you give; otherwise it lists every transmission, newest first, and waits for your choice. Resume preserves transmissions and starts no work. To delete one, ask for it like any item.

> [!NOTE]
> nestor plugs in the only MCP server in the house: `https://journal.mcp-marketplace.org/mcp`

</details>

### 💾 nestor-beta · for coders

Nestor learned to code. It takes you from an idea to merged pull requests. Install it **on top of** nestor.

<p align="center">
  <img src=".github/assets/parcours.svg" width="100%" alt="A board game: your idea, then spec turns it into tasks, build turns a task into a pull request, ship merges it into main, doctor closes the shipped tasks. Shortcut when you do not know what to do next: next-tasks finds the project through Git, or takes the one you name, and lists its tasks to do now.">
</p>

Two ways in. **New idea?** Start with `spec`. **Not sure what to do next?** Run `next-tasks`: in a repo it finds the project through Git, anywhere else you name it (`/nestor-beta:next-tasks lisbon-trip`), and it lists what to do now.

- 📐 `/nestor-beta:spec` — turns your idea into a task tree, one question at a time
- 📋 `/nestor-beta:next-tasks` — lists a project’s active tasks
- 🏗️ `/nestor-beta:build` — turns a task into a pull request
- 🚢 `/nestor-beta:ship` — merges open PRs into `main` (`ship list` only looks)
- 🩺 `/nestor-beta:doctor` — offers to close tasks that already shipped
- 🧹 `/nestor-beta:clean-task` — tidies up a task
- 🔄 `/nestor-beta:check-for-updates` — looks for an update

Behind the scenes, 🔗 `nestor-beta` signs your pull requests with a `nestor tasks:` footer. Nothing to type.

### 🎭 massdo-skills · for style

Changes how your agent talks to you. A style stays on until `reset`.

- ✂️ `/massdo-skills:answer-short` — short answers, 120 words max
- ✍️ `/massdo-skills:articulate` — full sentences that connect
- 🎯 `/massdo-skills:chief-of-staff` — decides instead of handing you a menu
- 📡 `/massdo-skills:extract-signal` — sorts raw text, then acts on it (`raw` returns the sorted text only)

<br>

<p align="center"><sub>🏛️ Made by massdo</sub></p>
