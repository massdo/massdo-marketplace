#!/usr/bin/env bash
set -u

plugin=nestor@massdo-marketplace
endpoint=https://journal.mcp-marketplace.org/mcp
origin=https://journal.mcp-marketplace.org
required_skills='["nestor","activity","tree","explain","pause","resume","check-for-updates"]'
clients=()
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
pending_reason=
gum_bin=
gum_version=0.17.0
spinner_pid=
spinner_flag=
menu_tty=
cursor_plugin="$HOME/.cursor/plugins/local/nestor"
cursor_mcp="$HOME/.cursor/mcp.json"
cursor_server_marker="$cursor_plugin/.massdo-mcp-server"

# The braces also silence the shell's own "Terminated" notice for the job.
stop_process() {
    {
        kill "$1" || :
        sleep 0.2
        kill -KILL "$1" || :
        wait "$1" || :
    } 2>/dev/null
}

# A spinner is gum spin waiting for a flag file; stopping it creates the file,
# so it ends cleanly even from a shell that is not its parent.
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

cleanup_processes() {
    spinner_stop
    [ -z "$app_pid" ] || stop_process "$app_pid"
    [ -z "$command_pid" ] || stop_process "$command_pid"
}

cleanup() {
    cleanup_processes
    menu_restore
    [ -z "$scratch" ] || rm -rf -- "$scratch"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

show_client_error() {
    if [ -n "$client_error" ] && [ -s "$client_error" ]; then tail -n 12 "$client_error" >&2; fi
}

# Result lines go to stdout; the marks are colored only on a terminal. That is
# decided once, here: tint mostly runs inside $(...), where stdout is a pipe.
colors=false
[ ! -t 1 ] || colors=true
tint() { if [ "$colors" = true ]; then printf '\033[%sm%s\033[0m' "$1" "$2"; else printf '%s' "$2"; fi; }
say() { printf '%s\n' "$*"; }

fail() { spinner_stop; printf '%s\n' "$*" >&2; show_client_error; exit 1; }

# Each app ends with one of these two results, in its own subshell.
succeed() {
    spinner_stop
    say "  $(tint 32 '✔') Nestor is installed and connected to your account."
    exit 0
}

incomplete() {
    spinner_stop
    [ -z "$pending_reason" ] || say "  $pending_reason"
    say "  $(tint 33 '⚠') Nestor is installed — finish connecting your account"
    local command='codex mcp login nestor'
    case "$client" in
        claude) command='claude mcp login plugin:nestor:nestor' ;;
        cursor) command="${binary##*/} mcp login nestor" ;;
    esac
    if [ "${1:-}" = retry ]; then
        printf '%s\n' "$verification_error" >&2
        show_client_error
        if [ "$client" = cursor ]; then
            say '  Try again: reload Cursor or restore your Nestor connection, then run this setup command again.'
        else
            say '  Try again: restore your connection to Nestor, then run this setup command again.'
        fi
        say "  If you are asked to sign in afterward, run: $command"
        exit 2
    fi
    say "  To continue, run: $command"
    say '  Then run this setup command again to check the connection.'
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

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi
}

verify_checksum() {
    local actual
    actual=$(sha256_of "$1") || fail 'Cannot check the SHA-256 checksum.'
    [ "${actual%% *}" = "$2" ] || fail "$3"
}

ensure_jq() {
    if command -v jq >/dev/null 2>&1; then
        jq_bin=$(command -v jq)
        return
    fi
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
        "https://github.com/jqlang/jq/releases/download/jq-1.8.1/$asset" -o "$jq_bin" || fail 'Cannot download jq. Check your internet connection and try again.'
    verify_checksum "$jq_bin" "$digest" 'The jq download failed its SHA-256 checksum check.'
    chmod 700 "$jq_bin"
}

# The spinners and the sign-in question are drawn by gum (charmbracelet/gum),
# pinned by version and SHA-256 like jq. It is only needed when the setup
# command has to ask which apps to set up; a run with --client never downloads it.
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
        if grep -Eiq 'needs authentication|requires authentication|not authenticated|authentication required|login required' "$scratch/tools" "$scratch/tools.err"; then return 2; fi
        return 3
    fi
    verification_error='Required Nestor tools are missing from Cursor.'
    grep -Eq '(^|[^[:alnum:]_])get_item([^[:alnum:]_]|$)' "$scratch/tools"
}

# Cursor Agent only connects to servers listed in ~/.cursor/mcp.json, so the
# plugin copy alone is invisible to it. The entry is added once, remembered by
# a marker, and removed by uninstall.sh only when that marker is present.
cursor_add_server() {
    local current='{}' updated
    if [ -f "$cursor_mcp" ]; then
        json -e 'type == "object"' "$cursor_mcp" >/dev/null || fail 'Cannot read the Cursor MCP configuration (~/.cursor/mcp.json).'
        current=$(cat "$cursor_mcp")
        if printf '%s' "$current" | json -e '.mcpServers.nestor != null' >/dev/null; then return 0; fi
    fi
    updated=$(printf '%s' "$current" | json --arg url "$endpoint" '.mcpServers = (.mcpServers // {}) + {nestor: {type: "http", url: $url}}') ||
        fail 'Cannot update the Cursor MCP configuration.'
    mkdir -p "${cursor_mcp%/*}" || fail 'Cannot create the Cursor configuration directory.'
    printf '%s\n' "$updated" >"$cursor_mcp.nestor-tmp" && mv -- "$cursor_mcp.nestor-tmp" "$cursor_mcp" ||
        fail 'Cannot write the Cursor MCP configuration.'
    printf '%s\n' "$endpoint" >"$cursor_server_marker"
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

plugin_state() {
    if [ "$client" = codex ]; then
        # Without a marketplace name, Codex also refreshes its remote plugin
        # catalog, which can take longer than the time budget on a cold cache.
        capture 30 "$scratch/plugins.json" "$binary" plugin list --json -m massdo-marketplace || return 1
        json -e '.installed | type == "array"' "$scratch/plugins.json" >/dev/null || return 1
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

# Cursor Agent echoes the first characters of the OAuth authorization code it
# received; its sign-in output reaches the terminal without that line. A flag
# file marks the end of the relay, so the wizard's next line waits for it.
relay_login_output() {
    local line
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in *'Received authorization code '*) continue ;; esac
        printf '%s\n' "$line" >&3
    done
    : >"$scratch/login-relayed"
}

relay_login_wait() {
    local ticks=0
    [ "$client" = cursor ] || return 0
    while [ ! -e "$scratch/login-relayed" ] && [ "$ticks" -lt 50 ]; do
        sleep 0.1
        ticks=$((ticks + 1))
    done
}

# Keystrokes typed before the sign-in are discarded first. Codex also reads a
# pasted callback URL from a terminal and cancels the sign-in on a bare Enter,
# so it gets a pipe held open instead: nothing to read, and the browser
# callback alone completes the sign-in.
login() {
    local server=nestor deadline=$((SECONDS + 300)) result
    [ "$client" != claude ] || server=plugin:nestor:nestor
    flush_terminal_input
    if [ "$client" = codex ]; then
        mkfifo "$scratch/login-input" || return 1
        exec 6<>"$scratch/login-input"
        NO_COLOR=1 "$binary" mcp login "$server" <&6 >&3 2>&3 &
    elif [ "$client" = cursor ]; then
        rm -f "$scratch/login-relayed"
        NO_COLOR=1 "$binary" mcp login "$server" <&3 > >(relay_login_output) 2>&1 &
    else
        NO_COLOR=1 "$binary" mcp login "$server" <&3 >&3 2>&3 &
    fi
    command_pid=$!
    while kill -0 "$command_pid" 2>/dev/null; do
        if [ "$SECONDS" -ge "$deadline" ]; then
            stop_process "$command_pid"
            command_pid=
            exec 6>&-
            relay_login_wait
            return 124
        fi
        sleep 0.1
    done
    wait "$command_pid"; result=$?
    command_pid=
    exec 6>&-
    relay_login_wait
    return "$result"
}

# Asks before opening the native OAuth flow; the menu tool draws the question
# when it is available, otherwise the terminal reads one line.
ask_login() {
    local answer
    if [ -n "$gum_bin" ]; then
        "$gum_bin" confirm 'Open your browser to connect Nestor?' <&3 2>&3
        return $?
    fi
    printf '%s' 'Open your browser to connect Nestor? (y/N): ' >&3
    IFS= read -r answer <&3 || return 1
    case "$answer" in o|O|oui|y|Y|yes) return 0 ;; *) return 1 ;; esac
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

client_label() {
    case "$1" in
        codex) printf '%s' 'Codex' ;;
        claude) printf '%s' 'Claude Code' ;;
        cursor) printf '%s' 'Cursor Agent' ;;
    esac
}

client_icon() {
    case "$1" in
        codex) tint '38;5;36' '◉' ;;
        claude) tint '38;5;173' '✳' ;;
        cursor) tint '38;5;33' '⬢' ;;
    esac
}

client_binary() {
    if [ "$1" = cursor ]; then command -v cursor-agent || command -v agent; else command -v "$1"; fi
}

add_client() {
    local name existing
    case "$1" in
        codex|claude|cursor) ;;
        *) fail 'Choose codex, claude or cursor.' ;;
    esac
    for existing in ${clients[@]+"${clients[@]}"}; do [ "$existing" != "$1" ] || return 0; done
    clients+=("$1")
}

# One line per app for the menu: what the app already has, read without
# changing anything. Collisions and unreadable inventories are reported here
# as a state and again, in full, when the app is set up.
inventory() {
    local target=$1 state
    case "$target" in
        cursor)
            state=$( scratch="$scratch/menu-$target"; mkdir -p "$scratch" || exit 1; client=$target
                     cursor_state 2>/dev/null && printf '%s' "$installed" )
            case "$state" in
                true) printf '%s' 'installed' ;;
                false) printf '%s' 'not installed' ;;
                *) printf '%s' 'existing files are not from this setup' ;;
            esac
            return ;;
    esac
    state=$( scratch="$scratch/menu-$target"; mkdir -p "$scratch" || exit 1; client=$target
             binary=$(client_binary "$target") || exit 1
             plugin_state 2>/dev/null || exit 1
             printf '%s %s %s' "$installed" "$enabled" "$(json -r '.[0].version // ""' "$scratch/selected.json")" )
    set -- $state
    case "${1:-}/${2:-}" in
        true/true) printf '%s' "installed${3:+ $3}" ;;
        true/*) printf '%s' 'installed but disabled' ;;
        false/*) printf '%s' 'not installed' ;;
        *) printf '%s' 'status unknown' ;;
    esac
}

# The menu is drawn here, not by gum: gum choose cannot check an app with Enter
# and stay open, and starting it again after each Enter made the menu blink.
# Each key redraws the same lines in place, with line wrapping off so that a
# narrow terminal clips them instead of shifting the redraw. Between keys the
# cursor waits on the first line, so closing the menu erases it from there.
menu_restore() {
    [ -n "$menu_tty" ] || return 0
    printf '\033[J\033[?7h\033[?25h' >&3
    stty "$menu_tty" <&3 2>/dev/null || :
    menu_tty=
}

# Enter on an app checks or unchecks it; Enter on the last line starts the
# setup of the checked apps.
choose_clients() {
    local candidates=() labels=() checked=() rows=() candidate state shown index cursor=0 key rest
    local frame notice= timeout=1
    # The menu is drawn on the terminal, whatever stdout is.
    local colors=true
    local header help on pointer launch
    header=$(tint '38;5;117' 'Where should Nestor be installed?')
    help=$(tint 90 'Use ↑↓ to move and Enter to check an app, then choose Launch install.')
    on=$(tint '38;5;117' '☑')
    pointer=$(tint '38;5;117' '> ')
    launch=$(tint 1 '▶ Launch install')
    printf '%s\n' 'Looking for your apps…' >&3
    command -v codex >/dev/null 2>&1 && candidates+=(codex)
    command -v claude >/dev/null 2>&1 && candidates+=(claude)
    command -v cursor-agent >/dev/null 2>&1 && candidates+=(cursor)
    [ "${#candidates[@]}" -gt 0 ] || fail 'Install Codex, Claude Code or Cursor Agent, then run this setup command again.'
    ensure_gum
    for candidate in "${candidates[@]}"; do
        spinner_start "Checking $(client_label "$candidate")"
        state=$(inventory "$candidate")
        spinner_stop
        case "$state" in installed*) shown=$(tint 32 "$state") ;; *) shown=$state ;; esac
        labels+=("$(client_icon "$candidate") $(client_label "$candidate") — $shown")
        case "$state" in
            'not installed'|'installed but disabled') checked+=(true) ;;
            *) checked+=(false) ;;
        esac
    done
    [ "${BASH_VERSINFO[0]}" -lt 4 ] || timeout=0.1
    flush_terminal_input
    menu_tty=$(stty -g <&3) && stty -echo -icanon <&3 || fail 'Cannot read keys from this terminal.'
    printf '\033[?25l\033[?7l' >&3
    while :; do
        rows=()
        for index in "${!candidates[@]}"; do
            if [ "${checked[$index]}" = true ]; then rows+=("$on ${labels[$index]}"); else rows+=("☐ ${labels[$index]}"); fi
        done
        rows+=("$launch")
        frame=$'\033[2K'"$header"$'\n\033[2K'"${notice:-$help}"$'\n'
        for index in "${!rows[@]}"; do
            if [ "$index" -eq "$cursor" ]; then
                frame="$frame"$'\033[2K'"$pointer$(tint '38;5;117' "${rows[$index]}")"$'\n'
            else
                frame="$frame"$'\033[2K'"  ${rows[$index]}"$'\n'
            fi
        done
        printf '%s' "$frame" >&3
        # Back to the first line: the next frame overwrites this one.
        printf '\033[%sA' "$((${#rows[@]} + 2))" >&3
        IFS= read -rsn1 key <&3 || key=$'\033'
        case "$key" in
            $'\033')
                rest=
                IFS= read -rsn2 -t "$timeout" rest <&3 || :
                case "$rest" in
                    '[A'|OA) cursor=$(((cursor + ${#rows[@]} - 1) % ${#rows[@]})) ;;
                    '[B'|OB) cursor=$(((cursor + 1) % ${#rows[@]})) ;;
                    '')
                        menu_restore
                        fail 'App selection was interrupted. Run this setup command again.' ;;
                esac ;;
            k) cursor=$(((cursor + ${#rows[@]} - 1) % ${#rows[@]})) ;;
            j) cursor=$(((cursor + 1) % ${#rows[@]})) ;;
            '')
                notice=
                if [ "$cursor" -lt "${#candidates[@]}" ]; then
                    if [ "${checked[$cursor]}" = true ]; then checked[$cursor]=false; else checked[$cursor]=true; fi
                    continue
                fi
                for index in "${!candidates[@]}"; do
                    [ "${checked[$index]}" = false ] || add_client "${candidates[$index]}"
                done
                if [ "${#clients[@]}" -gt 0 ]; then
                    menu_restore
                    return 0
                fi
                notice=$(tint 33 'Check at least one app, then choose Launch install.') ;;
        esac
    done
}

installed_version() {
    local version
    if [ "$client" = cursor ]; then
        version=$(json -r '.version // ""' "$cursor_plugin/.cursor-plugin/plugin.json")
    else
        version=$(json -r '.[0].version // ""' "$scratch/selected.json")
    fi
    [ -z "$version" ] || printf ' %s' "$version"
}

# Checks the connection, offers the native sign-in once, and ends the app with
# its result: connected, installed but not connected, or failed.
finish() {
    local status
    spinner_start 'Verifying the Nestor connection'
    verify; status=$?
    spinner_stop
    case "$status" in
        0) succeed ;;
        2) ;;
        3) incomplete retry ;;
        *) fail "$verification_error" ;;
    esac
    say '  Nestor is not connected to your account yet.'
    if [ "$check_only" = true ] || [ "$no_login" = true ] || [ "$terminal" = false ]; then incomplete; fi
    flush_terminal_input
    ask_login || { pending_reason='Browser sign-in skipped.'; incomplete; }
    say '  Opening your browser. Sign in, allow the connection, then come back to this window.'
    login || { pending_reason='The browser sign-in did not finish.'; incomplete; }
    spinner_start 'Verifying the Nestor connection'
    verify; status=$?
    spinner_stop
    case "$status" in
        0) succeed ;;
        2) pending_reason="$(client_label "$client") still reports Nestor as not signed in."; incomplete ;;
        3) incomplete retry ;;
        *) fail "$verification_error" ;;
    esac
}

# Runs in a subshell per app: fail, incomplete and succeed end that app only,
# and the exit code becomes the app's result in the summary.
run_client() {
    client=$1
    trap cleanup_processes EXIT
    scratch="$scratch/$client"
    mkdir -p "$scratch" || fail 'Cannot create a temporary folder.'
    binary=$(client_binary "$client") || fail "Client not found: $client."
    spinner_start "Checking $(client_label "$client")"
    capture 15 "$scratch/version" "$binary" --version || fail 'Cannot read the app version.'
    if [ "$client" = cursor ]; then
        capture 15 "$scratch/help" "$binary" mcp login --help || fail 'This Cursor Agent version cannot connect to Nestor.'
        capture 15 "$scratch/help" "$binary" mcp list-tools --help || fail 'This Cursor Agent version cannot check Nestor tools.'
        cursor_state
        spinner_stop
        [ "$installed" = false ] || say "  Nestor$(installed_version) is already installed."
        if [ "$check_only" = false ]; then
            if [ "$installed" = false ]; then
                spinner_start 'Installing Nestor in Cursor'
                cursor_install
                spinner_stop
                say '  Nestor installed.'
            fi
            cursor_add_server
        fi
        finish
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
    spinner_stop
    if [ "$installed" = true ] && [ "$enabled" = true ]; then say "  Nestor$(installed_version) is already installed."; fi
    if [ "$check_only" = false ]; then
        action=
        if [ "$installed" = false ]; then action=installed; elif [ "$enabled" = false ]; then action=enabled; fi
        spinner_start "Installing Nestor in $(client_label "$client")"
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
        spinner_stop
        [ -z "$action" ] || say "  Nestor $action."
    fi
    finish
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --client)
            [ "$#" -ge 2 ] || fail 'Missing value for --client. Choose codex, claude or cursor.'
            IFS=, read -r -a names <<< "$2"
            for name in ${names[@]+"${names[@]}"}; do add_client "$name"; done
            shift 2 ;;
        --check) check_only=true; shift ;;
        --no-login) no_login=true; shift ;;
        --help|-h) printf '%s\n' 'Usage: install.sh [--client codex|claude|cursor]... [--check] [--no-login]'; exit 0 ;;
        *) fail "Unknown option: $1" ;;
    esac
done
for name in ${clients[@]+"${clients[@]}"}; do
    client_binary "$name" >/dev/null || fail "Client not found: $name."
done
{ exec 3<>/dev/tty; } 2>/dev/null && terminal=true
if [ "${#clients[@]}" -eq 0 ] && [ "$terminal" = false ]; then
    fail 'Without a terminal, specify --client codex, claude or cursor.'
fi
case "$(uname -s)-$(uname -m)" in Darwin-arm64|Darwin-x86_64|Linux-aarch64|Linux-arm64|Linux-x86_64) ;; *) fail 'This computer architecture is not supported.' ;; esac
umask 077
scratch=$(mktemp -d "${TMPDIR:-/tmp}/nestor-install.XXXXXX") || fail 'Cannot create a temporary folder.'
cd "$scratch" || exit 1
ensure_jq
[ "${#clients[@]}" -gt 0 ] || choose_clients
failed=false
pending=false
summary=
apps=
for name in "${clients[@]}"; do
    printf '%s\n' "$(client_icon "$name") $(client_label "$name")"
    ( run_client "$name" ); status=$?
    printf '\n'
    # Each line reads like the menu: the app's icon and name, then its state.
    case "$status" in
        0) line=$(tint 32 '✔ installed and connected') ;;
        2) pending=true; line=$(tint 33 '⚠ finish connecting your account') ;;
        *) failed=true; line=$(tint 31 '✖ not set up — see the message above') ;;
    esac
    summary="$summary$(client_icon "$name") $(client_label "$name") — $line
"
    case "$apps" in
        '') apps=$(client_label "$name") ;;
        *) apps="$apps, $(client_label "$name")" ;;
    esac
done
apps=$(printf '%s' "$apps" | sed 's/\(.*\), /\1 or /')
if [ "${#clients[@]}" -gt 1 ]; then
    printf '%s\n' "$(tint '38;5;117' 'Summary')"
    printf '%s\n' "$summary"
fi
if [ "$failed" = true ]; then
    printf '%s\n' 'Setup did not finish. Fix the problem shown above, then run this setup command again.'
    exit 1
fi
if [ "$pending" = true ]; then
    printf '%s\n' 'Nestor is installed but not connected to your account yet. Follow the steps above, then run this setup command again.'
    exit 2
fi
printf '%s\n' "$(tint 32 'Installation complete')"
printf '%s\n' "Open a new conversation in $apps and type: Show my tasks."
exit 0
