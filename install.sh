#!/usr/bin/env bash
set -u

plugin=nestor@massdo-marketplace
endpoint=https://journal.mcp-marketplace.org/mcp
origin=https://journal.mcp-marketplace.org
required_skills='["nestor","activity","tree","pause","resume","check-for-updates"]'
client=
check_only=false
no_login=false
scratch=
app_pid=
command_pid=
terminal=false
installed=false
enabled=false
verification_error=
client_error=
cursor_plugin="$HOME/.cursor/plugins/local/nestor"

stop_process() {
    kill "$1" 2>/dev/null || :
    sleep 0.2
    kill -KILL "$1" 2>/dev/null || :
    wait "$1" 2>/dev/null || :
}

cleanup() {
    [ -z "$app_pid" ] || stop_process "$app_pid"
    [ -z "$command_pid" ] || stop_process "$command_pid"
    [ -z "$scratch" ] || rm -rf -- "$scratch"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

show_client_error() {
    if [ -n "$client_error" ] && [ -s "$client_error" ]; then tail -n 12 "$client_error" >&2; fi
}

fail() { printf '%s\n' "$*" >&2; show_client_error; exit 1; }
incomplete() {
    printf '%s\n' 'Nestor is installed — finish connecting your account'
    local command='codex mcp login nestor'
    case "$client" in
        claude) command='claude mcp login plugin:nestor:nestor' ;;
        cursor) command="${binary##*/} mcp login nestor" ;;
    esac
    if [ "${1:-}" = retry ]; then
        printf '%s\n' "$verification_error" >&2
        show_client_error
        if [ "$client" = cursor ]; then
            printf '%s\n' 'Try again: reload Cursor or restore your Nestor connection, then run this setup command again.'
        else
            printf '%s\n' 'Try again: restore your connection to Nestor, then run this setup command again.'
        fi
        printf '%s\n' "If you are asked to sign in afterward, run: $command"
        exit 2
    fi
    printf '%s\n' "To continue, run: $command"
    printf '%s\n' 'Then run this setup command again to check the connection.'
    exit 2
}

capture() {
    local limit=$1 destination=$2 deadline result
    shift 2
    client_error=
    NO_COLOR=1 "$@" </dev/null >"$destination" 2>"$destination.err" &
    command_pid=$!
    deadline=$((SECONDS + limit))
    while kill -0 "$command_pid" 2>/dev/null; do
        if [ "$SECONDS" -ge "$deadline" ]; then
            stop_process "$command_pid"
            command_pid=
            client_error="$destination.err"
            printf '%s\n' "The app did not respond in time ($limit s)." >>"$client_error"
            return 124
        fi
        sleep 0.1
    done
    wait "$command_pid"; result=$?
    command_pid=
    [ "$result" -eq 0 ] || client_error="$destination.err"
    return "$result"
}

ensure_jq() {
    if command -v jq >/dev/null 2>&1; then
        jq_bin=$(command -v jq)
        return
    fi
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
        "https://github.com/jqlang/jq/releases/download/jq-1.8.1/$asset" -o "$jq_bin" || fail 'Cannot download jq. Check your internet connection and try again.'
    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$jq_bin")
    else
        actual=$(shasum -a 256 "$jq_bin") || fail 'Cannot check the SHA-256 checksum.'
    fi
    [ "${actual%% *}" = "$digest" ] || fail 'The jq download failed its SHA-256 checksum check.'
    chmod 700 "$jq_bin"
}

json() { "$jq_bin" "$@" 2>/dev/null; }

rpc() {
    local id=$1 request=$2 line remaining deadline=$((SECONDS + 45))
    printf '%s\n' "$request" >&4
    while [ "$SECONDS" -lt "$deadline" ]; do
        remaining=$((deadline - SECONDS))
        IFS= read -r -t "$remaining" line <&5 || return 1
        if printf '%s' "$line" | json -e --argjson id "$id" '.id == $id' >/dev/null 2>&1; then
            printf '%s' "$line" >"$scratch/reply.json"
            json -e 'has("result") and (has("error") | not)' "$scratch/reply.json" >/dev/null 2>&1
            return $?
        fi
    done
    return 1
}

codex_probe() {
    verification_error='Cannot communicate with Codex to check Nestor.'
    rpc 1 '{"id":1,"method":"initialize","params":{"clientInfo":{"name":"nestor_installer","version":"1.0.0"},"capabilities":{"experimentalApi":true}}}' || return 1
    printf '%s\n' '{"method":"initialized"}' >&4
    verification_error='Nestor skills are missing, disabled or unreadable.'
    rpc 2 '{"id":2,"method":"skills/list","params":{"forceReload":true}}' || return 1
    json -e --argjson required "$required_skills" '[.result.data[].skills[] | select(.enabled == true) | .name] as $names | $required | all(. as $name | $names | index("nestor:" + $name) != null)' "$scratch/reply.json" >/dev/null || return 1
    verification_error='Cannot check the Nestor server.'
    rpc 3 '{"id":3,"method":"mcpServerStatus/list","params":{"serverName":"nestor","detail":"toolsAndAuthOnly","limit":100}}' || return 1
    verification_error='The Nestor server is missing or has an unexpected identity.'
    json -ce --arg plugin "$plugin" --arg origin "$origin" '[.result.data[] | select(.name == "nestor" and .pluginId == $plugin and .httpOrigin == $origin)] | if length == 1 then .[0] else error("Invalid server identity") end' "$scratch/reply.json" >"$scratch/status.json" || return 1
    if json -e '.authStatus == "notLoggedIn" or .runtimeStatus == "authRequired"' "$scratch/status.json" >/dev/null; then return 2; fi
    verification_error='Cannot verify the Nestor sign-in status.'
    json -e '.authStatus == "oAuth"' "$scratch/status.json" >/dev/null || return 1
    verification_error='Cannot reach Nestor or load its tools.'
    json -e '.toolsError == null and (.runtimeStatus == null or .runtimeStatus == "connected")' "$scratch/status.json" >/dev/null || return 3
    verification_error='Required Nestor tools are missing from the server response.'
    json -e '[.tools[].name] | index("get_item") != null' "$scratch/status.json" >/dev/null || return 1
    return 0
}

codex_check() {
    verification_error='Cannot find or check the Nestor server.'
    capture 20 "$scratch/server.json" "$binary" mcp get nestor --json || return 1
    verification_error='The Nestor server is disabled or uses a different URL.'
    json -e --arg url "$endpoint" '.enabled == true and .transport.url == $url' "$scratch/server.json" >/dev/null || return 1
    verification_error='Cannot open the connection used to check Codex.'
    mkfifo "$scratch/rpc-in" "$scratch/rpc-out" || return 1
    exec 4<>"$scratch/rpc-in"
    "$binary" app-server --stdio <"$scratch/rpc-in" >"$scratch/rpc-out" 2>"$scratch/app-server.err" &
    app_pid=$!
    exec 5<>"$scratch/rpc-out"
    local result
    codex_probe; result=$?
    exec 4>&- 5>&-
    stop_process "$app_pid"
    app_pid=
    [ "$result" -eq 0 ] || client_error="$scratch/app-server.err"
    rm -f "$scratch/rpc-in" "$scratch/rpc-out"
    return "$result"
}

claude_check() {
    verification_error='Cannot read the list of Nestor skills.'
    capture 30 "$scratch/details" "$binary" plugin details "$plugin" || return 1
    sed $'s/\033\\[[0-9;]*m//g' "$scratch/details" >"$scratch/details-plain"
    local skill
    verification_error='Nestor skills are missing or disabled.'
    for skill in $(printf '%s' "$required_skills" | json -r '.[]'); do
        sed -n '/^[[:space:]]*Skills ([0-9][0-9]*)/p' "$scratch/details-plain" | grep -Eq "(^|[ ,])$skill([ ,]|$)" || return 1
    done
    local result url
    verification_error='Cannot reach or check the Nestor server.'
    capture 45 "$scratch/connection" "$binary" mcp get plugin:nestor:nestor; result=$?
    sed $'s/\033\\[[0-9;]*m//g' "$scratch/connection" >"$scratch/connection-plain"
    [ "$(grep -c '^[[:space:]]*URL:' "$scratch/connection-plain")" = 1 ] || return 1
    url=$(sed -n 's/^[[:space:]]*URL:[[:space:]]*//p' "$scratch/connection-plain" | sed 's/[[:space:]]*$//')
    [ "$url" = "$endpoint" ] || fail 'Collision: the plugin server uses a different URL.'
    [ "$(grep -c '^[[:space:]]*Status:' "$scratch/connection-plain")" = 1 ] || return 1
    if grep -Eq '^[[:space:]]*Status: .*Needs authentication[[:space:]]*$' "$scratch/connection-plain"; then return 2; fi
    if grep -Eq '^[[:space:]]*Status: (.*Failed to connect|.*Connected · tools fetch failed)[[:space:]]*$' "$scratch/connection-plain"; then return 3; fi
    [ "$result" -eq 0 ] && grep -Eq '^[[:space:]]*Status: ✔ Connected[[:space:]]*$' "$scratch/connection-plain"
}

cursor_state() {
    installed=false
    if [ -f "$HOME/.cursor/mcp.json" ]; then
        json -e --arg url "$endpoint" '.mcpServers.nestor == null or .mcpServers.nestor.url == $url' \
            "$HOME/.cursor/mcp.json" >/dev/null ||
            fail 'Collision: the existing Cursor nestor server has a different configuration.'
    fi
    if [ -e "$cursor_plugin" ] || [ -L "$cursor_plugin" ]; then
        [ -d "$cursor_plugin" ] && [ ! -L "$cursor_plugin" ] &&
            [ "$(cat "$cursor_plugin/.massdo-installer" 2>/dev/null)" = 'massdo/massdo-marketplace:install.sh:v1' ] ||
            fail 'Collision: the Cursor Nestor plugin was not installed by this setup command.'
        installed=true
    fi
}

cursor_check() {
    verification_error='The Nestor plugin is missing from Cursor.'
    cursor_state
    [ "$installed" = true ] || return 1
    verification_error='The Cursor Nestor plugin is incomplete or has a different server URL.'
    json -e '.name == "nestor"' "$cursor_plugin/.cursor-plugin/plugin.json" >/dev/null || return 1
    json -e --arg url "$endpoint" '.mcpServers.nestor.url == $url' "$cursor_plugin/mcp.json" >/dev/null || return 1
    local skill
    for skill in $(printf '%s' "$required_skills" | json -r '.[]'); do
        [ -f "$cursor_plugin/skills/$skill/SKILL.md" ] || return 1
    done
    verification_error='Cannot reach Nestor or load its tools in Cursor.'
    if ! capture 45 "$scratch/tools" "$binary" mcp list-tools nestor; then
        if grep -Eiq 'needs authentication|not authenticated|authentication required|login required' "$scratch/tools" "$scratch/tools.err"; then return 2; fi
        return 3
    fi
    verification_error='Required Nestor tools are missing from Cursor.'
    grep -Eq '(^|[^[:alnum:]_])get_item([^[:alnum:]_]|$)' "$scratch/tools"
}

cursor_install() {
    command -v git >/dev/null 2>&1 || fail 'Git is required to install Nestor for Cursor.'
    capture 120 "$scratch/clone-log" git clone --depth 1 --quiet https://github.com/massdo/massdo-marketplace.git "$scratch/repo" ||
        fail 'Cannot download the Nestor plugin.'
    [ -f "$scratch/repo/plugins/nestor/.cursor-plugin/plugin.json" ] || fail 'The downloaded Cursor plugin is incomplete.'
    local parent stage
    parent=${cursor_plugin%/*}
    mkdir -p "$parent" || fail 'Cannot create the Cursor plugin directory.'
    stage=$(mktemp -d "$parent/.nestor-install.XXXXXX") || fail 'Cannot stage the Cursor plugin.'
    if ! cp -R "$scratch/repo/plugins/nestor/." "$stage/"; then rm -rf -- "$stage"; fail 'Cannot copy the Cursor plugin.'; fi
    printf '%s\n' 'massdo/massdo-marketplace:install.sh:v1' >"$stage/.massdo-installer"
    if ! mv -- "$stage" "$cursor_plugin"; then rm -rf -- "$stage"; fail 'Cannot activate the Cursor plugin.'; fi
}

grokbot_detected() {
    [ -d '/Applications/Grok Bot.app' ] || [ -d "$HOME/Applications/Grok Bot.app" ] ||
        [ -f "$HOME/.local/share/applications/grok-bot.desktop" ] ||
        [ -f "$HOME/.local/share/applications/grokbot.desktop" ] ||
        [ -f '/usr/share/applications/grok-bot.desktop' ] ||
        [ -f '/usr/share/applications/grokbot.desktop' ]
}

grokbot_instructions() {
    printf '%s\n' 'Grok Bot detected. Finish Nestor setup in the Grok Bot app:'
    printf '%s\n' '1. Open Connect apps and add a custom Remote HTTPS MCP server named nestor.'
    printf '%s\n' "2. Use this server URL: $endpoint"
    printf '%s\n' '3. Sign in to Nestor in the browser, then verify that get_item is available.'
    printf '%s\n' 'This installer cannot read or change plugins in your Grok Bot cloud account.'
    exit 2
}

plugin_state() {
    if [ "$client" = codex ]; then
        capture 30 "$scratch/plugins.json" "$binary" plugin list --json || return 1
        json -e '.installed | type == "array"' "$scratch/plugins.json" >/dev/null || return 1
        json -e '[.installed[] | select((.pluginId | startswith("nestor@")) and .pluginId != "nestor@massdo-marketplace")] | length == 0' "$scratch/plugins.json" >/dev/null || fail 'Collision: an existing Nestor plugin comes from a different marketplace.'
        json -ce '[.installed[] | select(.pluginId == "nestor@massdo-marketplace")]' "$scratch/plugins.json" >"$scratch/selected.json" || return 1
    else
        capture 30 "$scratch/plugins.json" "$binary" plugin list --json || return 1
        json -e 'type == "array"' "$scratch/plugins.json" >/dev/null || return 1
        json -e '[.[] | select(.scope != "synced" and (.id | startswith("nestor@")) and (.id != "nestor@massdo-marketplace" or .scope != "user"))] | length == 0' "$scratch/plugins.json" >/dev/null || fail 'Collision: an existing Nestor installation has a different source or scope.'
        json -ce '[.[] | select(.id == "nestor@massdo-marketplace" and .scope == "user")]' "$scratch/plugins.json" >"$scratch/selected.json" || return 1
    fi
    json -e 'length <= 1' "$scratch/selected.json" >/dev/null || return 1
    installed=$(json -r 'length == 1' "$scratch/selected.json")
    enabled=$(json -r '.[0].enabled == true' "$scratch/selected.json")
}

marketplace_state() {
    capture 30 "$scratch/marketplaces.json" "$binary" plugin marketplace list --json || return 1
    if [ "$client" = codex ]; then
        json -ce '.marketplaces | arrays | [.[] | select(.name == "massdo-marketplace")]' "$scratch/marketplaces.json" >"$scratch/marketplace.json" || return 1
        json -e 'all(.marketplaceSource.sourceType == "git" and (.marketplaceSource.source == "https://github.com/massdo/massdo-marketplace.git" or .marketplaceSource.source == "https://github.com/massdo/massdo-marketplace"))' "$scratch/marketplace.json" >/dev/null || fail 'Collision: the marketplace uses a different source.'
    else
        json -ce 'arrays | [.[] | select(.name == "massdo-marketplace")]' "$scratch/marketplaces.json" >"$scratch/marketplace.json" || return 1
        json -e 'all(.source == "github" and .repo == "massdo/massdo-marketplace")' "$scratch/marketplace.json" >/dev/null || fail 'Collision: the marketplace uses a different source.'
    fi
    json -e 'length <= 1' "$scratch/marketplace.json" >/dev/null || fail 'Collision: multiple marketplaces have the same name.'
    marketplace=$(json -r 'length == 1' "$scratch/marketplace.json")
}

server_collision() {
    if [ "$client" = codex ]; then
        capture 30 "$scratch/servers.json" "$binary" mcp list --json || return 1
        json -e 'type == "array"' "$scratch/servers.json" >/dev/null || return 1
        json -e --arg url "$endpoint" --argjson installed "$installed" '[.[] | select(.name == "nestor")] | length <= 1 and all($installed and .transport.url == $url)' "$scratch/servers.json" >/dev/null || fail 'Collision: the existing nestor server has a different configuration.'
    else
        if capture 30 "$scratch/manual-server" "$binary" mcp get nestor; then
            fail 'Collision: a nestor server already exists outside the plugin.'
        fi
        if [ "$installed" = false ] && capture 30 "$scratch/manual-server" "$binary" mcp get plugin:nestor:nestor; then
            fail 'Collision: an existing server already uses the plugin name.'
        fi
    fi
}

abort_installation() {
    fail "$*"
}

login() {
    local server=nestor deadline=$((SECONDS + 300)) result
    [ "$client" != claude ] || server=plugin:nestor:nestor
    NO_COLOR=1 "$binary" mcp login "$server" <&3 >&3 2>&3 &
    command_pid=$!
    while kill -0 "$command_pid" 2>/dev/null; do
        if [ "$SECONDS" -ge "$deadline" ]; then
            stop_process "$command_pid"
            command_pid=
            return 124
        fi
        sleep 0.1
    done
    wait "$command_pid"; result=$?
    command_pid=
    return "$result"
}

verify() {
    if [ "$client" = cursor ]; then cursor_check; return $?; fi
    verification_error='Cannot read the installed plugins in your app.'
    plugin_state || return 1
    verification_error='The Nestor plugin is not installed.'
    [ "$installed" = true ] || return 1
    verification_error='The Nestor plugin is disabled. Run setup without --check to enable it.'
    [ "$enabled" = true ] || return 1
    if [ "$client" = codex ]; then codex_check; else claude_check; fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --client) [ "$#" -ge 2 ] || fail 'Missing value for --client. Choose codex, claude, cursor or grokbot.'; client=$2; shift 2 ;;
        --check) check_only=true; shift ;;
        --no-login) no_login=true; shift ;;
        --help|-h) printf '%s\n' 'Usage: install.sh [--client codex|claude|cursor|grokbot] [--check] [--no-login]'; exit 0 ;;
        *) fail "Unknown option: $1" ;;
    esac
done
{ exec 3<>/dev/tty; } 2>/dev/null && terminal=true
if [ -z "$client" ]; then
    [ "$terminal" = true ] || fail 'Without a terminal, specify --client codex, claude, cursor or grokbot.'
    choices=()
    command -v codex >/dev/null 2>&1 && choices+=(codex)
    command -v claude >/dev/null 2>&1 && choices+=(claude)
    command -v cursor-agent >/dev/null 2>&1 && choices+=(cursor)
    grokbot_detected && choices+=(grokbot)
    [ "${#choices[@]}" -gt 0 ] || fail 'Install Codex, Claude Code, Cursor Agent or Grok Bot, then run this setup command again.'
    if [ "${#choices[@]}" -eq 1 ]; then client=${choices[0]}; else
        printf 'Choose your app (%s): ' "$(IFS=/; printf '%s' "${choices[*]}")" >&3
        IFS= read -r client <&3 || fail 'App selection was interrupted. Run this setup command again.'
        for choice in "${choices[@]}"; do [ "$client" != "$choice" ] || break; done
        [ "$client" = "$choice" ] || fail 'Choose one of the detected apps.'
    fi
fi
case "$client" in codex|claude|cursor|grokbot) ;; *) fail 'Choose codex, claude, cursor or grokbot.' ;; esac
[ "$client" != grokbot ] || grokbot_instructions
if [ "$client" = cursor ]; then binary=$(command -v cursor-agent || command -v agent) || fail 'Cursor Agent CLI not found.'
else binary=$(command -v "$client") || fail "Client not found: $client."; fi
case "$(uname -s)-$(uname -m)" in Darwin-arm64|Darwin-x86_64|Linux-aarch64|Linux-arm64|Linux-x86_64) ;; *) fail 'This computer architecture is not supported.' ;; esac
umask 077
scratch=$(mktemp -d "${TMPDIR:-/tmp}/nestor-install.XXXXXX") || fail 'Cannot create a temporary folder.'
cd "$scratch" || exit 1
ensure_jq
capture 15 "$scratch/version" "$binary" --version || fail 'Cannot read the app version.'
if [ "$client" = cursor ]; then
    capture 15 "$scratch/help" "$binary" mcp login --help || fail 'This Cursor Agent version cannot connect to Nestor.'
    capture 15 "$scratch/help" "$binary" mcp list-tools --help || fail 'This Cursor Agent version cannot check Nestor tools.'
    cursor_state
    if [ "$check_only" = false ] && [ "$installed" = false ]; then cursor_install; fi
    verify; verification_status=$?
    if [ "$verification_status" -eq 0 ]; then printf '%s\n' 'Installation complete'; exit 0; fi
    [ "$verification_status" -ne 3 ] || incomplete retry
    [ "$verification_status" -eq 2 ] || fail "$verification_error"
    if [ "$check_only" = true ] || [ "$no_login" = true ] || [ "$terminal" = false ]; then incomplete; fi
    printf '%s' 'Open your browser to connect Nestor? (y/N): ' >&3
    IFS= read -r answer <&3 || incomplete
    case "$answer" in o|O|oui|y|Y|yes) ;; *) incomplete ;; esac
    login || incomplete
    verify && { printf '%s\n' 'Installation complete'; exit 0; }
    incomplete
fi
for capability in 'plugin list' 'plugin marketplace list' 'plugin marketplace add' 'mcp login'; do
    # Capability names are fixed here, never supplied by the caller.
    capture 15 "$scratch/help" "$binary" $capability --help || fail 'This app version is not supported. Update your app, then run this setup command again.'
done
if [ "$client" = codex ]; then
    capture 15 "$scratch/help" "$binary" plugin add --help || fail 'This app version cannot install plugins. Update your app and try again.'
    capture 15 "$scratch/help" "$binary" app-server --help || fail 'This Codex version has no app-server command. Update Codex and try again.'
else
    capture 15 "$scratch/help" "$binary" plugin install --help || fail 'This app version cannot install plugins. Update your app and try again.'
    capture 15 "$scratch/help" "$binary" plugin enable --help || fail 'This app version cannot enable plugins. Update your app and try again.'
    capture 15 "$scratch/help" "$binary" plugin details --help || fail 'This app version cannot list skills. Update your app and try again.'
fi
plugin_state || fail 'Cannot read the installed plugins in your app.'
marketplace_state || abort_installation 'Cannot read the marketplaces in your app.'
server_collision || abort_installation 'Cannot check the MCP server configuration.'
if [ "$check_only" = false ]; then
    if [ "$marketplace" = false ]; then
        capture 120 "$scratch/add-marketplace" "$binary" plugin marketplace add massdo/massdo-marketplace || abort_installation 'Cannot add the marketplace. Check the error below, then run this setup command again.'
        marketplace_state && [ "$marketplace" = true ] || abort_installation 'The marketplace is still missing after setup tried to add it.'
    fi
    if [ "$installed" = false ] || [ "$enabled" = false ]; then
        if [ "$client" = codex ]; then
            # The native add command also enables an existing plugin; it does not run OAuth.
            capture 120 "$scratch/add-plugin" "$binary" plugin add "$plugin" --json
        elif [ "$installed" = true ]; then
            capture 120 "$scratch/add-plugin" "$binary" plugin enable "$plugin" --scope user
        else
            capture 120 "$scratch/add-plugin" "$binary" plugin install "$plugin" --scope user
        fi
        result=$?
        [ "$result" -eq 0 ] || abort_installation 'Cannot install or enable Nestor. Check the error below, then run this setup command again.'
        installed=true
        plugin_state || abort_installation 'Cannot check Nestor after installing it.'
        [ "$installed" = true ] && [ "$enabled" = true ] || abort_installation 'Cannot install or enable Nestor. Check the error below, then run this setup command again.'
    fi
fi
verify; verification_status=$?
if [ "$verification_status" -eq 0 ]; then printf '%s\n' 'Installation complete'; exit 0; fi
[ "$verification_status" -ne 3 ] || incomplete retry
[ "$verification_status" -eq 2 ] || fail "$verification_error"
if [ "$check_only" = true ] || [ "$no_login" = true ] || [ "$terminal" = false ]; then incomplete; fi
printf '%s' 'Open your browser to connect Nestor? (y/N): ' >&3
IFS= read -r answer <&3 || incomplete
case "$answer" in o|O|oui|y|Y|yes) ;; *) incomplete ;; esac
login || incomplete
verify; verification_status=$?
if [ "$verification_status" -eq 0 ]; then printf '%s\n' 'Installation complete'; exit 0; fi
[ "$verification_status" -ne 3 ] || incomplete retry
[ "$verification_status" -eq 2 ] || fail "$verification_error"
incomplete
