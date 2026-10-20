#!/usr/bin/env bash
set -u

plugin=nestor@massdo-marketplace
endpoint=https://journal.mcp-marketplace.org/mcp
client=
terminal=false
scratch=
cursor_plugin="$HOME/.cursor/plugins/local/nestor"

cleanup() { [ -z "$scratch" ] || rm -rf -- "$scratch"; }
trap cleanup EXIT
fail() { printf '%s\n' "$*" >&2; exit 1; }

ensure_jq() {
    if command -v jq >/dev/null 2>&1; then jq_bin=$(command -v jq); return; fi
    local asset digest actual
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
    if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$jq_bin")
    else actual=$(shasum -a 256 "$jq_bin") || fail 'Cannot check the SHA-256 checksum.'; fi
    [ "${actual%% *}" = "$digest" ] || fail 'The jq download failed its SHA-256 checksum check.'
    chmod 700 "$jq_bin"
}

json() { "$jq_bin" "$@" 2>/dev/null; }

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

while [ "$#" -gt 0 ]; do
    case "$1" in
        --client) [ "$#" -ge 2 ] || fail 'Missing value for --client.'; client=$2; shift 2 ;;
        --help|-h) printf '%s\n' 'Usage: uninstall.sh [--client codex|claude|cursor|grokbot]'; exit 0 ;;
        *) fail "Unknown option: $1" ;;
    esac
done

{ exec 3<>/dev/tty; } 2>/dev/null && terminal=true
if [ -z "$client" ]; then
    [ "$terminal" = true ] || fail 'Without a terminal, specify --client codex, claude, cursor or grokbot.'
    choices=()
    command -v codex >/dev/null 2>&1 && choices+=(codex)
    command -v claude >/dev/null 2>&1 && choices+=(claude)
    if command -v cursor-agent >/dev/null 2>&1 ||
        [ -e "$cursor_plugin" ] || [ -L "$cursor_plugin" ]; then choices+=(cursor); fi
    grokbot_detected && choices+=(grokbot)
    [ "${#choices[@]}" -gt 0 ] || fail 'No supported app detected.'
    if [ "${#choices[@]}" -eq 1 ]; then client=${choices[0]}; else
        printf 'Remove Nestor from which app (%s): ' "$(IFS=/; printf '%s' "${choices[*]}")" >&3
        IFS= read -r client <&3 || fail 'App selection was interrupted.'
        for choice in "${choices[@]}"; do [ "$client" != "$choice" ] || break; done
        [ "$client" = "$choice" ] || fail 'Choose one of the detected apps.'
    fi
fi

case "$client" in
    codex|claude|cursor|grokbot) ;;
    *) fail 'Choose codex, claude, cursor or grokbot.' ;;
esac

if [ "$client" = grokbot ]; then
    printf '%s\n' 'To remove Nestor from Grok Bot, open Connect apps → Your plugins.'
    printf '%s\n' 'Remove the custom Remote HTTPS MCP server named nestor and confirm it disappears from Installed.'
    printf '%s\n' 'Grok Bot stores plugins in your cloud account; this local command cannot remove them.'
    exit 2
fi

if [ "$client" = cursor ]; then
    if [ ! -e "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ]; then
        printf '%s\n' 'No wizard-managed Nestor plugin is installed in Cursor.'
        exit 0
    fi
    [ -d "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ] &&
        [ "$(cat "$cursor_plugin/.massdo-installer" 2>/dev/null)" = 'massdo/massdo-marketplace:install.sh:v1' ] ||
        fail 'The Cursor Nestor plugin was not installed by this wizard; it was left untouched.'
    rm -rf -- "$cursor_plugin" || fail 'Cannot remove the Cursor Nestor plugin.'
    [ ! -e "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ] || fail 'The Cursor Nestor plugin is still present.'
    printf '%s\n' 'Nestor removed from Cursor. Reload Cursor or start a new Cursor Agent session.'
    printf '%s\n' 'If a separate marketplace copy remains in Customize, remove it there.'
    exit 0
fi

binary=$(command -v "$client") || fail "Client not found: $client."
scratch=$(mktemp -d "${TMPDIR:-/tmp}/nestor-uninstall.XXXXXX") || fail 'Cannot create a temporary folder.'
ensure_jq
"$binary" plugin list --json >"$scratch/plugins.json" 2>"$scratch/error" || {
    tail -n 12 "$scratch/error" >&2
    fail 'Cannot inspect installed plugins.'
}
if ! plugin_present "$scratch/plugins.json"; then
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
printf '%s\n' "Nestor removed from $client. Start a new session to apply the change."
