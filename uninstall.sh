#!/usr/bin/env bash
set -u

plugin=nestor@massdo-marketplace
endpoint=https://journal.mcp-marketplace.org/mcp
clients=()
client=
terminal=false
scratch=
gum_bin=
gum_version=0.17.0
spinner_pid=
spinner_flag=
cursor_plugin="$HOME/.cursor/plugins/local/nestor"
cursor_mcp="$HOME/.cursor/mcp.json"
cursor_server_marker="$cursor_plugin/.massdo-mcp-server"

# A spinner is gum spin waiting for a flag file; stopping it creates the file.
spinner_start() {
    [ -n "$gum_bin" ] && [ "$terminal" = true ] || return 0
    spinner_flag="$scratch/spinner-$$-$RANDOM"
    rm -f "$spinner_flag"
    "$gum_bin" spin --spinner dot --spinner.foreground=117 --title="$1" \
        -- sh -c 'while [ ! -e "$1" ]; do sleep 0.1; done' _ "$spinner_flag" </dev/null 2>&3 >/dev/null &
    spinner_pid=$!
}

spinner_stop() {
    [ -n "$spinner_pid" ] || return 0
    : >"$spinner_flag"
    wait "$spinner_pid" 2>/dev/null || :
    spinner_pid=
}

cleanup() { spinner_stop; [ -z "$scratch" ] || rm -rf -- "$scratch"; }
trap cleanup EXIT
fail() { spinner_stop; printf '%s\n' "$*" >&2; exit 1; }

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi
}

verify_checksum() {
    local actual
    actual=$(sha256_of "$1") || fail 'Cannot check the SHA-256 checksum.'
    [ "${actual%% *}" = "$2" ] || fail "$3"
}

ensure_jq() {
    if command -v jq >/dev/null 2>&1; then jq_bin=$(command -v jq); return; fi
    local asset digest
    case "$(uname -s)-$(uname -m)" in
        Darwin-arm64) asset=jq-macos-arm64; digest=a9fe3ea2f86dfc72f6728417521ec9067b343277152b114f4e98d8cb0e263603 ;;
        Darwin-x86_64) asset=jq-macos-amd64; digest=e80dbe0d2a2597e3c11c404f03337b981d74b4a8504b70586c354b7697a7c27f ;;
        Linux-aarch64|Linux-arm64) asset=jq-linux-arm64; digest=6bc62f25981328edd3cfcfe6fe51b073f2d7e7710d7ef7fcdac28d4e384fc3d4 ;;
        Linux-x86_64) asset=jq-linux-amd64; digest=020468de7539ce70ef1bceaf7cde2e8c4f2ca6c3afb84642aabc5c97d9fc2a0d ;;
        *) fail 'This computer architecture is not supported.' ;;
    esac
    jq_bin="$scratch/jq"
    curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 60 \
        "https://github.com/jqlang/jq/releases/download/jq-1.8.1/$asset" -o "$jq_bin" || fail 'Cannot download jq.'
    verify_checksum "$jq_bin" "$digest" 'The jq download failed its SHA-256 checksum check.'
    chmod 700 "$jq_bin"
}

# Same pinned menu tool as install.sh; only needed to ask which apps to clean.
ensure_gum() {
    if command -v gum >/dev/null 2>&1 && gum choose --help 2>&1 | grep -q -- '--label-delimiter'; then
        gum_bin=$(command -v gum)
        return
    fi
    local asset digest directory
    case "$(uname -s)-$(uname -m)" in
        Darwin-arm64) asset=Darwin_arm64; digest=e2a4b8596efa05821d8c58d0c1afbcd7ad1699ba69c689cc3ff23a4a99c8b237 ;;
        Darwin-x86_64) asset=Darwin_x86_64; digest=cd66576aeebe6cd19c771863c7e8d696e0e1d5387d1e7075666baa67c2052e53 ;;
        Linux-aarch64|Linux-arm64) asset=Linux_arm64; digest=b0b9ed95cbf7c8b7073f17b9591811f5c001e33c7cfd066ca83ce8a07c576f9c ;;
        Linux-x86_64) asset=Linux_x86_64; digest=69ee169bd6387331928864e94d47ed01ef649fbfe875baed1bbf27b5377a6fdb ;;
        *) fail 'This computer architecture is not supported.' ;;
    esac
    directory="$scratch/gum"
    mkdir -p "$directory" || fail 'Cannot create a temporary folder.'
    printf '%s\n' 'Downloading the menu tool' >&3
    curl --fail --progress-bar --show-error --location --proto '=https' --tlsv1.2 --max-time 120 \
        "https://github.com/charmbracelet/gum/releases/download/v$gum_version/gum_${gum_version}_$asset.tar.gz" \
        -o "$directory/gum.tar.gz" 2>&3 || fail 'Cannot download the menu tool. Check your internet connection and try again.'
    verify_checksum "$directory/gum.tar.gz" "$digest" 'The menu tool download failed its SHA-256 checksum check.'
    tar -xzf "$directory/gum.tar.gz" -C "$directory" || fail 'Cannot unpack the menu tool.'
    gum_bin="$directory/gum_${gum_version}_$asset/gum"
    [ -x "$gum_bin" ] || fail 'The menu tool is missing from its archive.'
}

json() { "$jq_bin" "$@" 2>/dev/null; }

# Keystrokes typed while the apps were being checked would otherwise reach the
# menu as answers; they are discarded first.
flush_terminal_input() {
    local junk timeout=1
    [ "${BASH_VERSINFO[0]}" -lt 4 ] || timeout=0.2
    while IFS= read -r -t "$timeout" -n 1 junk <&3; do :; done
}

plugin_present() {
    local file=$1
    if [ "$client" = codex ]; then
        json -e '.installed | type == "array"' "$file" >/dev/null || fail 'Invalid Codex plugin inventory.'
        json -e --arg plugin "$plugin" '.installed | any(.[]; .pluginId == $plugin)' "$file" >/dev/null
    else
        json -e 'type == "array"' "$file" >/dev/null || fail 'Invalid Claude Code plugin inventory.'
        json -e --arg plugin "$plugin" 'any(.[]; .id == $plugin and .scope == "user")' "$file" >/dev/null
    fi
}

grokbot_detected() {
    [ -d '/Applications/Grok Bot.app' ] || [ -d "$HOME/Applications/Grok Bot.app" ] ||
        [ -f "$HOME/.local/share/applications/grok-bot.desktop" ] ||
        [ -f "$HOME/.local/share/applications/grokbot.desktop" ] ||
        [ -f '/usr/share/applications/grok-bot.desktop' ] ||
        [ -f '/usr/share/applications/grokbot.desktop' ]
}

cursor_owned() {
    [ -d "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ] &&
        [ "$(cat "$cursor_plugin/.massdo-installer" 2>/dev/null)" = 'massdo/massdo-marketplace:install.sh:v1' ]
}

client_label() {
    case "$1" in
        codex) printf '%s' 'Codex' ;;
        claude) printf '%s' 'Claude Code' ;;
        cursor) printf '%s' 'Cursor' ;;
        grokbot) printf '%s' 'Grok Bot' ;;
    esac
}

client_icon() {
    case "$1" in
        codex) printf '\033[38;5;36m◉\033[0m' ;;
        claude) printf '\033[38;5;173m✳\033[0m' ;;
        cursor) printf '\033[38;5;33m⬢\033[0m' ;;
        grokbot) printf '\033[1;38;5;245mX\033[0m' ;;
    esac
}

# Removes the ~/.cursor/mcp.json entry only when install.sh added it.
cursor_remove_server() {
    local updated
    [ -f "$cursor_server_marker" ] && [ -f "$cursor_mcp" ] || return 0
    json -e --arg url "$endpoint" '.mcpServers.nestor.url == $url' "$cursor_mcp" >/dev/null || return 0
    updated=$(json 'del(.mcpServers.nestor)' "$cursor_mcp") || fail 'Cannot update the Cursor MCP configuration.'
    printf '%s\n' "$updated" >"$cursor_mcp.nestor-tmp" && mv -- "$cursor_mcp.nestor-tmp" "$cursor_mcp" ||
        fail 'Cannot write the Cursor MCP configuration.'
}

add_client() {
    local existing
    case "$1" in
        codex|claude|cursor|grokbot) ;;
        *) fail 'Choose codex, claude, cursor or grokbot.' ;;
    esac
    for existing in ${clients[@]+"${clients[@]}"}; do [ "$existing" != "$1" ] || return 0; done
    clients+=("$1")
}

# One line per app for the menu, read without changing anything.
inventory() {
    local target=$1 file
    case "$target" in
        grokbot) printf '%s' 'set up in your Grok account'; return ;;
        cursor)
            if [ ! -e "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ]; then printf '%s' 'not installed'
            elif cursor_owned; then printf '%s' 'installed by this setup'
            else printf '%s' 'existing files are not from this setup'; fi
            return ;;
    esac
    file="$scratch/menu-$target.json"
    if ! "$target" plugin list --json >"$file" 2>/dev/null; then printf '%s' 'status unknown'; return; fi
    case "$( client=$target; plugin_present "$file" 2>/dev/null; printf '%s' "$?" )" in
        0) printf '%s' 'installed' ;;
        1) printf '%s' 'not installed' ;;
        *) printf '%s' 'status unknown' ;;
    esac
}

choose_clients() {
    local candidates=() options=() preselected= candidate state shown label selection option
    local green=$'\033[32m' reset=$'\033[0m'
    printf '%s\n' 'Looking for your apps…' >&3
    command -v codex >/dev/null 2>&1 && candidates+=(codex)
    command -v claude >/dev/null 2>&1 && candidates+=(claude)
    if command -v cursor-agent >/dev/null 2>&1 ||
        [ -e "$cursor_plugin" ] || [ -L "$cursor_plugin" ]; then candidates+=(cursor); fi
    grokbot_detected && candidates+=(grokbot)
    [ "${#candidates[@]}" -gt 0 ] || fail 'No supported app detected.'
    ensure_gum
    for candidate in "${candidates[@]}"; do
        spinner_start "Checking $(client_label "$candidate")"
        state=$(inventory "$candidate")
        spinner_stop
        case "$state" in installed*) shown="$green$state$reset" ;; *) shown=$state ;; esac
        label="$(client_icon "$candidate") $(client_label "$candidate") — $shown"
        options+=("$label|$candidate")
        case "$state" in
            installed|'installed by this setup') preselected="$preselected${preselected:+,}$label" ;;
        esac
    done
    flush_terminal_input
    selection=$("$gum_bin" choose --no-limit --label-delimiter='|' \
        --header='Remove Nestor from which apps?' \
        --header.foreground=117 --cursor.foreground=117 --selected.foreground=117 \
        --selected="$preselected" "${options[@]}" <&3 2>&3) || fail 'App selection was interrupted.'
    while IFS= read -r option; do [ -z "$option" ] || add_client "$option"; done <<EOT
$selection
EOT
    if [ "${#clients[@]}" -eq 0 ]; then
        printf '%s\n' 'Nothing selected. Nestor was left in place.'
        exit 0
    fi
}

# Runs in a subshell per app: fail ends that app only.
remove_client() {
    client=$1
    scratch="$scratch/$client"
    mkdir -p "$scratch" || fail 'Cannot create a temporary folder.'
    if [ "$client" = grokbot ]; then
        printf '%s\n' 'Grok Bot keeps its connectors in your Grok account, so this command cannot remove Nestor for you.'
        printf '%s\n' '1. Open https://grok.com/connectors and remove the custom connector that uses:'
        printf '%s\n' "   $endpoint"
        printf '%s\n' '2. In Grok Bot, open Connect apps and check that nestor is gone.'
        exit 2
    fi
    if [ "$client" = cursor ]; then
        if [ ! -e "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ]; then
            printf '%s\n' 'No wizard-managed Nestor plugin is installed in Cursor.'
            exit 0
        fi
        cursor_owned || fail 'The Cursor Nestor plugin was not installed by this wizard; it was left untouched.'
        cursor_remove_server
        rm -rf -- "$cursor_plugin" || fail 'Cannot remove the Cursor Nestor plugin.'
        [ ! -e "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ] || fail 'The Cursor Nestor plugin is still present.'
        printf '%s\n' 'Nestor removed from Cursor. Reload Cursor or start a new Cursor Agent session.'
        printf '%s\n' 'If a separate marketplace copy remains in Customize, remove it there.'
        exit 0
    fi
    local binary
    binary=$(command -v "$client") || fail "Client not found: $client."
    spinner_start "Removing Nestor from $(client_label "$client")"
    "$binary" plugin list --json >"$scratch/plugins.json" 2>"$scratch/error" || {
        tail -n 12 "$scratch/error" >&2
        fail 'Cannot inspect installed plugins.'
    }
    if ! plugin_present "$scratch/plugins.json"; then
        spinner_stop
        printf '%s\n' "Nestor is already absent from $client."
        exit 0
    fi
    if [ "$client" = codex ]; then
        if "$binary" mcp get nestor --json >"$scratch/server.json" 2>/dev/null &&
            json -e --arg url "$endpoint" '.transport.url == $url' "$scratch/server.json" >/dev/null; then
            "$binary" mcp logout nestor >/dev/null 2>&1 || :
        fi
        "$binary" plugin remove "$plugin" --json >"$scratch/remove.json" 2>"$scratch/error" || {
            tail -n 12 "$scratch/error" >&2
            fail 'Cannot remove Nestor from Codex.'
        }
    else
        "$binary" mcp logout plugin:nestor:nestor >/dev/null 2>&1 || :
        "$binary" plugin uninstall "$plugin" --scope user --json >"$scratch/remove.json" 2>"$scratch/error" || {
            tail -n 12 "$scratch/error" >&2
            fail 'Cannot remove Nestor from Claude Code.'
        }
    fi
    "$binary" plugin list --json >"$scratch/after.json" 2>"$scratch/error" || fail 'Nestor removal could not be verified.'
    if plugin_present "$scratch/after.json"; then fail 'Nestor is still installed.'; fi
    spinner_stop
    printf '%s\n' "Nestor removed from $client. Start a new session to apply the change."
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --client)
            [ "$#" -ge 2 ] || fail 'Missing value for --client.'
            IFS=, read -r -a names <<< "$2"
            for name in ${names[@]+"${names[@]}"}; do add_client "$name"; done
            shift 2 ;;
        --help|-h) printf '%s\n' 'Usage: uninstall.sh [--client codex|claude|cursor|grokbot]...'; exit 0 ;;
        *) fail "Unknown option: $1" ;;
    esac
done

{ exec 3<>/dev/tty; } 2>/dev/null && terminal=true
if [ "${#clients[@]}" -eq 0 ] && [ "$terminal" = false ]; then
    fail 'Without a terminal, specify --client codex, claude, cursor or grokbot.'
fi
scratch=$(mktemp -d "${TMPDIR:-/tmp}/nestor-uninstall.XXXXXX") || fail 'Cannot create a temporary folder.'
ensure_jq
[ "${#clients[@]}" -gt 0 ] || choose_clients
failed=false
pending=false
summary=
for name in "${clients[@]}"; do
    [ "${#clients[@]}" -eq 1 ] || printf '\n%s\n' "$(client_icon "$name") $(client_label "$name")"
    ( remove_client "$name" ); status=$?
    case "$status" in
        0) line='removed or already absent' ;;
        2) pending=true; line='finish the steps on grok.com' ;;
        *) failed=true; line='not removed — see the message above' ;;
    esac
    summary="$summary$(client_label "$name"): $line
"
done
if [ "${#clients[@]}" -gt 1 ]; then
    printf '\n%s\n' 'Summary'
    printf '%s' "$summary"
fi
[ "$failed" = false ] || exit 1
[ "$pending" = false ] || exit 2
exit 0
