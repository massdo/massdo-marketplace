# Nestor installation

For Codex and Claude Code, the installer adds `nestor@massdo-marketplace` through
native marketplace and plugin commands. For Cursor Agent on Mac or Linux, it
copies `plugins/nestor/` into Cursor's user-local plugin directory and checks
MCP tool access with the native CLI. It installs Nestor only. Apps whose
connectors live in an online account, such as Grok Bot or claude.ai, are set up
in their own interface and are not offered by the wizard.

## Prerequisites

- Install Codex, Claude Code, or Cursor Agent first.
  On Windows, the PowerShell wizard currently supports Codex and Claude Code;
  expose their native executable on
  `PATH`; `.cmd`, `.bat` and `.ps1` launchers are refused without running a shell.
- Install Git, which the clients use to retrieve the marketplace.
- Bash: macOS or Linux, including WSL, on x86_64 or arm64, with Bash 3.2+ and curl.
  The script uses an existing jq or downloads official jq 1.8.1 temporarily. It
  checks the pinned SHA-256 before execution and removes the temporary directory.
  A SHA-256 utility (`sha256sum` or `shasum`) is required for that download.
- Windows: Windows PowerShell 5.1+ or PowerShell 7. JSON parsing uses
  `ConvertFrom-Json` and requires no extra package.
- Allow HTTPS access to GitHub, the marketplace and Nestor's native OAuth flow.

The installer requires no Node.js, npm, npx or Python. Development tests use Python.
The reference client versions are Codex 0.163.0 and Claude Code 2.1.303. The script
checks command capabilities and validates response shapes rather than comparing
version strings. A client with missing commands stops before configuration changes.

## Start

macOS, Linux or WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/massdo/massdo-marketplace/main/install.sh | bash
```

To select one client:

```bash
curl -fsSL https://raw.githubusercontent.com/massdo/massdo-marketplace/main/install.sh | bash -s -- --client codex
```

Windows:

```powershell
$installerPath = Join-Path ([IO.Path]::GetTempPath()) ('nestor-' + [guid]::NewGuid() + '.ps1')
try {
    Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/massdo/massdo-marketplace/main/install.ps1' -OutFile $installerPath
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -Client codex
} finally {
    Remove-Item -LiteralPath $installerPath -ErrorAction SilentlyContinue
}
```

Use `claude` or `cursor` instead of `codex` as needed. `--client` may
be repeated or given a comma-separated list; every listed app is set up in turn,
and the exit code is the worst result (1 over 2 over 0). Without `--client`, the
Bash wizard detects installed Codex, Claude Code and Cursor Agent CLIs, reads
each app's plugin inventory
without changing it, and shows one menu of checkboxes: apps that already have
Nestor are marked with their version, apps without it are checked. Enter checks
or unchecks the app under the cursor, and Enter on the last line, `Launch
install`, sets up the checked apps. Each app
check, download and installation step shows a spinner. The menu
is drawn by [gum](https://github.com/charmbracelet/gum), pinned to version 0.17.0
and checked by SHA-256 like jq; it is downloaded to the temporary folder only when
no gum with `--label-delimiter` and `--no-show-help` is on `PATH`, and never when
`--client` is given.
Keystrokes typed while the apps are being checked are discarded before the menu
opens, so a stray Enter cannot change the preselection.
Bash reads the terminal separately from piped script content. Without a terminal,
the client selection is required and the installer leaves OAuth for a later native
login.
With a terminal, the installer asks before opening native OAuth. Answer `y` to
continue. `--no-login` or `-NoLogin` skips that prompt. Keystrokes typed before
the prompt and before the sign-in are discarded. `codex mcp login` also reads a
pasted callback URL from a terminal and cancels the sign-in on a bare Enter, so
the wizard gives it a pipe held open instead: the browser callback alone
completes the sign-in, and its `Callback URL (input hidden)` prompt can be ignored.
The Windows command downloads the file without decoding its UTF-8 BOM, then starts
a child PowerShell process. Its exit code cannot close the calling console. The
temporary file is removed when that child process ends.

## Result and recovery

Each app prints its own result under its name: what was found (`Nestor 0.9.1 is
already installed.`) or done (`Nestor installed.`), then `✔ Nestor is installed
and connected to your account.` or `⚠ Nestor is installed — finish connecting
your account`, preceded by the reason (`Browser sign-in skipped.`, `The browser
sign-in did not finish.`, `Codex still reports Nestor as not signed in.`). With
several apps, a `Summary` repeats one line per app, with the icon and name the
menu showed (`◉ Codex — ✔ installed and connected`). The last line gives the
overall result:

| Exit code | Last line | Next action |
| --- | --- | --- |
| 0 | `Installation complete`, then the app(s) to open | Start a new client session to use Nestor. |
| 2 | `Nestor is installed but not connected to your account yet.` | Complete authentication, or restore server access and rerun the installer, as indicated above it. |
| 1 | `Setup did not finish.` after the error on stderr | Resolve the displayed cause, then rerun the installer. |

For Cursor, the wizard installs a tagged local copy at
`~/.cursor/plugins/local/nestor` and, because Cursor Agent only connects to
servers listed in `~/.cursor/mcp.json`, adds a `nestor` entry there when none
exists, remembered by a `.massdo-mcp-server` marker in the plugin copy. It then
checks the plugin files and asks Cursor Agent for `get_item`. A pre-existing
untagged directory or symlink, or a `nestor` entry with another URL, is left
untouched and reported as a collision. Cursor currently has no non-interactive
CLI command for plugin installation, so the wizard does not write into its
synced marketplace inventory. Reload Cursor or start a new Agent session if
needed.

Native resume commands:

```bash
codex mcp login nestor
claude mcp login plugin:nestor:nestor
cursor-agent mcp login nestor
```

Choose the command for the installed client. The client opens OAuth and owns token
storage and renewal. The installer never reads, copies or stores tokens. Refusing
or postponing consent leaves the plugin installed. A failed server connection or
tool discovery also leaves the plugin installed and returns exit code 2. It prints
the failing control and asks you to restore server access, then rerun the installer.
The native login command is shown only as a conditional next step if authentication
is subsequently required; a connection failure never starts OAuth automatically.
Missing skills, disabled plugins, invalid responses and configuration errors return
exit code 1. Failed native commands print their last 12 stderr lines; temporary
diagnostic files are removed on exit. PowerShell also reports unexpected process
exceptions. Rerunning the installer resumes missing steps, reuses a valid
connection and does not add duplicate marketplaces or plugins.

The installer checks the connection immediately after native plugin installation.
If installation already authenticated Nestor, it does not request another login.
On the reference versions, Codex's native `plugin add` enables an existing disabled
plugin. An isolated local Codex 0.163.0 installation with an empty `CODEX_HOME` and
file credential stores exercised marketplace and plugin installation, reported
`ON_INSTALL` in the native plugin inventory, and stopped at pending authentication
with `--no-login`. This did not exercise browser consent. Claude Code uses
`plugin enable --scope user` for an existing disabled plugin. The installer performs
at most one explicit native login per run.

A marketplace named `massdo-marketplace` must point to this GitHub repository.
Claude Code's accepted source is the native `github` entry for
`massdo/massdo-marketplace`. A different source, conflicting Nestor plugin, different
installation scope, or conflicting MCP server stops installation without replacing
the existing configuration. The installer runs its client commands from a temporary
directory and installs into the user's profile, outside project configuration.
Claude Code's `synced` inventory entries are excluded from collision checks and
installation targets. They can coexist with the user-scoped marketplace plugin.

## Check without configuration changes

From a downloaded checkout:

```bash
bash install.sh --client codex --check
bash install.sh --client claude --check
```

```powershell
& .\install.ps1 -Client codex -Check
& .\install.ps1 -Client claude -Check
```

These commands do not add or enable a plugin and do not start OAuth. They perform
native read probes, which may refresh the client's normal caches or connection.
The installer limits command duration and closes its app-server process afterward.

Codex verification starts `app-server --stdio`, initializes its protocol, checks
`skills/list`, and checks `mcpServerStatus/list`. It requires the active Nestor
skills, the expected plugin and endpoint, OAuth status, discovered `get_item`, and
no tool discovery error. Claude Code verification requires the enabled user plugin,
its complete skill inventory, and `claude mcp get plugin:nestor:nestor` reporting
the expected endpoint and a connected authenticated MCP exchange. No model
generation or journal content is used. Configuration alone cannot report success.
Only Codex's `notLoggedIn`/`authRequired` or Claude's `Needs authentication` result
offers immediate native login. A failed connection or tool discovery reports an
incomplete installation with retry instructions. Missing skills, a disabled plugin
or missing required tools report a verification error. `scripts/validate.py` checks the
embedded endpoint, origin and required skills against the plugin files.

Protocol references: [Codex app-server](https://learn.chatgpt.com/docs/app-server?surface=cli),
[plugin packaging](https://developers.openai.com/plugins/build/plugins), and
[Claude Code MCP](https://code.claude.com/docs/en/mcp).

## Remove Nestor

On macOS, Linux or WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/massdo/massdo-marketplace/main/uninstall.sh | bash
```

Use `bash uninstall.sh --client codex|claude|cursor` to select clients
without a terminal; `--client` may be repeated. With a terminal and no `--client`,
the wizard shows the same gum menu as setup, with the apps that have Nestor
preselected. The wizard removes the exact Codex or Claude Code plugin
and clears its native Nestor OAuth connection when available. It removes a
Cursor local plugin only when the marker from this installer is present, and the
`~/.cursor/mcp.json` entry only when the `.massdo-mcp-server` marker shows the
installer added it; it never deletes an unmarked plugin, symlink or server entry.
The shared marketplace and other plugins are preserved. A new app session or
reload may be needed after removal.

## Validation before publication

Run the offline client doubles with isolated state and no account credentials:

```bash
python3 -m unittest discover -s tests -p test_install.py -v
pwsh -NoProfile -File tests/test_install.ps1
```

The PowerShell test entry runs the same scenarios against `install.ps1`. Windows
tests compile native executable doubles with the system .NET Framework compiler;
macOS and Linux use executable Python doubles. The tests cover fresh installation,
rerun, disabled plugins, OAuth refusal and postponement, failed installation,
offline responses, absent clients, incompatible clients, no terminal, invalid
responses, configuration preservation and collisions. Interactive OAuth scenarios
use a pseudo-terminal on macOS and Linux. Windows tests cover noninteractive
installation and the incomplete/resume result; they do not claim browser consent.

`.github/workflows/test-installer.yml` runs Bash doubles on macOS and Linux and
PowerShell doubles on Windows with Windows PowerShell and PowerShell 7. WSL uses
the Linux entry point. These tests exercise orchestration, not a real OAuth server.

Before publishing the one-command entry points, manually validate a fresh user
profile on macOS, Linux, WSL and native Windows with each client. Verify browser
consent, refusal, a second run, recovery after network loss, the loaded skills and
the final authenticated MCP discovery. Keep that evidence separate from the
offline tests and from checks using an already authenticated account. A PR and
local checks do not prove that fresh-user matrix.
