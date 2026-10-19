#!/usr/bin/env bash
set -u

plugin=nestor@massdo-marketplace
endpoint=https://journal.mcp-marketplace.org/mcp
client=
check_only=false
no_login=false
scratch=
app_pid=
command_pid=
terminal=false
installed=false
enabled=false

cleanup() {
    [ -z "$app_pid" ] || kill "$app_pid" 2>/dev/null || :
    [ -z "$command_pid" ] || kill "$command_pid" 2>/dev/null || :
    [ -z "$scratch" ] || rm -rf -- "$scratch"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

fail() { printf '%s\n' "$*" >&2; exit 1; }
incomplete() {
    printf '%s\n' 'Plugin installé — connexion Nestor à terminer'
    if [ "$client" = codex ]; then
        printf '%s\n' 'Reprise : codex mcp login nestor'
    else
        printf '%s\n' 'Reprise : claude mcp login plugin:nestor:nestor'
    fi
    printf '%s\n' 'Relancez ensuite cet installateur pour vérifier la connexion.'
    exit 2
}

capture() {
    local limit=$1 destination=$2 deadline result
    shift 2
    NO_COLOR=1 "$@" </dev/null >"$destination" 2>/dev/null &
    command_pid=$!
    deadline=$((SECONDS + limit))
    while kill -0 "$command_pid" 2>/dev/null; do
        if [ "$SECONDS" -ge "$deadline" ]; then
            kill "$command_pid" 2>/dev/null || :
            wait "$command_pid" 2>/dev/null || :
            command_pid=
            return 124
        fi
        sleep 0.1
    done
    wait "$command_pid"; result=$?
    command_pid=
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
        *) fail 'Architecture non prise en charge.' ;;
    esac
    jq_bin="$scratch/jq"
    curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 60 \
        "https://github.com/jqlang/jq/releases/download/jq-1.8.1/$asset" -o "$jq_bin" || fail 'Téléchargement de jq impossible.'
    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$jq_bin")
    else
        actual=$(shasum -a 256 "$jq_bin") || fail 'Vérification SHA-256 indisponible.'
    fi
    [ "${actual%% *}" = "$digest" ] || fail 'La vérification SHA-256 de jq a échoué.'
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

codex_check() {
    capture 20 "$scratch/server.json" "$binary" mcp get nestor --json || return 1
    json -e --arg url "$endpoint" '.enabled == true and .transport.url == $url' "$scratch/server.json" >/dev/null || return 1
    mkfifo "$scratch/rpc-in" "$scratch/rpc-out" || return 1
    exec 4<>"$scratch/rpc-in"
    "$binary" app-server --stdio <"$scratch/rpc-in" >"$scratch/rpc-out" 2>/dev/null &
    app_pid=$!
    exec 5<>"$scratch/rpc-out"
    local success=false
    if rpc 1 '{"id":1,"method":"initialize","params":{"clientInfo":{"name":"nestor_installer","version":"1.0.0"},"capabilities":{"experimentalApi":true}}}'; then
        printf '%s\n' '{"method":"initialized"}' >&4
        if rpc 2 '{"id":2,"method":"skills/list","params":{"forceReload":true}}' &&
            json -e '[.result.data[].skills[] | select(.enabled == true) | .name] as $names | ["nestor:nestor","nestor:activity","nestor:tree","nestor:pause","nestor:resume","nestor:check-for-updates"] | all(. as $name | $names | index($name) != null)' "$scratch/reply.json" >/dev/null &&
            rpc 3 '{"id":3,"method":"mcpServerStatus/list","params":{"serverName":"nestor","detail":"toolsAndAuthOnly","limit":100}}' &&
            json -e '.result.data | any(.name == "nestor" and .pluginId == "nestor@massdo-marketplace" and .httpOrigin == "https://journal.mcp-marketplace.org" and .authStatus == "oAuth" and .toolsError == null and (.runtimeStatus == null or .runtimeStatus == "connected") and ([.tools[].name] | index("get_item") != null))' "$scratch/reply.json" >/dev/null; then
            success=true
        fi
    fi
    exec 4>&- 5>&-
    kill "$app_pid" 2>/dev/null || :
    wait "$app_pid" 2>/dev/null || :
    app_pid=
    rm -f "$scratch/rpc-in" "$scratch/rpc-out"
    [ "$success" = true ]
}

claude_check() {
    capture 30 "$scratch/details" "$binary" plugin details "$plugin" || return 1
    sed $'s/\033\\[[0-9;]*m//g' "$scratch/details" >"$scratch/details-plain"
    local skill
    for skill in nestor activity tree pause resume check-for-updates; do
        sed -n '/^[[:space:]]*Skills ([0-9][0-9]*)/p' "$scratch/details-plain" | grep -Eq "(^|[ ,])$skill([ ,]|$)" || return 1
    done
    capture 45 "$scratch/connection" "$binary" mcp get plugin:nestor:nestor || return 1
    sed $'s/\033\\[[0-9;]*m//g' "$scratch/connection" >"$scratch/connection-plain"
    grep -Eq '^[[:space:]]*Status: ✔ Connected[[:space:]]*$' "$scratch/connection-plain" &&
        grep -Eq '^[[:space:]]*URL: https://journal[.]mcp-marketplace[.]org/mcp[[:space:]]*$' "$scratch/connection-plain"
}

plugin_state() {
    if [ "$client" = codex ]; then
        capture 30 "$scratch/plugins.json" "$binary" plugin list --json || return 1
        json -e '.installed | type == "array"' "$scratch/plugins.json" >/dev/null || return 1
        json -e '[.installed[] | select((.pluginId | startswith("nestor@")) and .pluginId != "nestor@massdo-marketplace")] | length == 0' "$scratch/plugins.json" >/dev/null || fail 'Collision : un plugin Nestor provient d’une autre marketplace.'
        json -ce '[.installed[] | select(.pluginId == "nestor@massdo-marketplace")]' "$scratch/plugins.json" >"$scratch/selected.json" || return 1
    else
        capture 30 "$scratch/plugins.json" "$binary" plugin list --json || return 1
        json -e 'type == "array"' "$scratch/plugins.json" >/dev/null || return 1
        json -e '[.[] | select((.id | startswith("nestor@")) and (.id != "nestor@massdo-marketplace" or .scope != "user"))] | length == 0' "$scratch/plugins.json" >/dev/null || fail 'Collision : Nestor possède une autre source ou une autre portée.'
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
        json -e 'all(.marketplaceSource.sourceType == "git" and (.marketplaceSource.source == "https://github.com/massdo/massdo-marketplace.git" or .marketplaceSource.source == "https://github.com/massdo/massdo-marketplace"))' "$scratch/marketplace.json" >/dev/null || fail 'Collision : la marketplace possède une autre source.'
    else
        json -ce 'arrays | [.[] | select(.name == "massdo-marketplace")]' "$scratch/marketplaces.json" >"$scratch/marketplace.json" || return 1
        json -e 'all(.source == "github" and .repo == "massdo/massdo-marketplace")' "$scratch/marketplace.json" >/dev/null || fail 'Collision : la marketplace possède une autre source.'
    fi
    json -e 'length <= 1' "$scratch/marketplace.json" >/dev/null || fail 'Collision : plusieurs marketplaces portent le même nom.'
    marketplace=$(json -r 'length == 1' "$scratch/marketplace.json")
}

server_collision() {
    if [ "$client" = codex ]; then
        capture 30 "$scratch/servers.json" "$binary" mcp list --json || return 1
        json -e 'type == "array"' "$scratch/servers.json" >/dev/null || return 1
        json -e --arg url "$endpoint" --argjson installed "$installed" '[.[] | select(.name == "nestor")] | length <= 1 and all($installed and .transport.url == $url)' "$scratch/servers.json" >/dev/null || fail 'Collision : le serveur nestor possède une configuration existante différente.'
    else
        if capture 30 "$scratch/manual-server" "$binary" mcp get nestor; then
            fail 'Collision : un serveur nestor existe hors du plugin.'
        fi
        if [ "$installed" = false ] && capture 30 "$scratch/manual-server" "$binary" mcp get plugin:nestor:nestor; then
            fail 'Collision : un serveur possède déjà le nom du plugin.'
        fi
    fi
}

abort_installation() {
    [ "$installed" = false ] || incomplete
    fail "$*"
}

login() {
    local server=nestor deadline=$((SECONDS + 300)) result
    [ "$client" = codex ] || server=plugin:nestor:nestor
    NO_COLOR=1 "$binary" mcp login "$server" <&3 >&3 2>&3 &
    command_pid=$!
    while kill -0 "$command_pid" 2>/dev/null; do
        if [ "$SECONDS" -ge "$deadline" ]; then
            kill "$command_pid" 2>/dev/null || :
            wait "$command_pid" 2>/dev/null || :
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
    plugin_state && [ "$installed" = true ] && [ "$enabled" = true ] || return 1
    if [ "$client" = codex ]; then codex_check; else claude_check; fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --client) [ "$#" -ge 2 ] || fail 'Valeur manquante pour --client.'; client=$2; shift 2 ;;
        --check) check_only=true; shift ;;
        --no-login) no_login=true; shift ;;
        --help|-h) printf '%s\n' 'Usage: install.sh [--client codex|claude] [--check] [--no-login]'; exit 0 ;;
        *) fail "Option inconnue : $1" ;;
    esac
done
{ exec 3<>/dev/tty; } 2>/dev/null && terminal=true
if [ -z "$client" ]; then
    [ "$terminal" = true ] || fail 'Sans terminal, indiquez --client codex ou --client claude.'
    if command -v codex >/dev/null 2>&1 && command -v claude >/dev/null 2>&1; then
        printf '%s' 'Client à utiliser (codex/claude) : ' >&3
        IFS= read -r client <&3 || fail 'Choix interrompu.'
    elif command -v codex >/dev/null 2>&1; then client=codex
    elif command -v claude >/dev/null 2>&1; then client=claude
    else fail 'Installez Codex ou Claude Code, puis relancez cette commande.'
    fi
fi
case "$client" in codex|claude) ;; *) fail 'Client attendu : codex ou claude.' ;; esac
binary=$(command -v "$client") || fail "Client absent : $client."
case "$(uname -s)-$(uname -m)" in Darwin-arm64|Darwin-x86_64|Linux-aarch64|Linux-arm64|Linux-x86_64) ;; *) fail 'Architecture non prise en charge.' ;; esac
umask 077
scratch=$(mktemp -d "${TMPDIR:-/tmp}/nestor-install.XXXXXX") || fail 'Répertoire temporaire indisponible.'
cd "$scratch" || exit 1
ensure_jq
capture 15 "$scratch/version" "$binary" --version || fail 'Version du client indisponible.'
for capability in 'plugin list' 'plugin marketplace list' 'mcp login'; do
    # Capability names are fixed here, never supplied by the caller.
    capture 15 "$scratch/help" "$binary" $capability --help || fail 'Client incompatible : mettez le client à jour.'
done
if [ "$client" = codex ]; then
    capture 15 "$scratch/help" "$binary" app-server --help || fail 'Client incompatible : app-server manque.'
else
    capture 15 "$scratch/help" "$binary" plugin details --help || fail 'Client incompatible : inventaire des skills indisponible.'
fi
plugin_state || fail 'Impossible de lire les plugins du client.'
marketplace_state || abort_installation 'Impossible de lire les marketplaces du client.'
server_collision || abort_installation 'Impossible de vérifier la configuration MCP.'
if [ "$check_only" = false ]; then
    if [ "$marketplace" = false ]; then
        capture 120 "$scratch/add-marketplace" "$binary" plugin marketplace add massdo/massdo-marketplace || abort_installation 'Ajout de la marketplace impossible. Relancez cette commande.'
        marketplace_state && [ "$marketplace" = true ] || abort_installation 'La marketplace ajoutée reste introuvable.'
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
        plugin_state || abort_installation 'Impossible de vérifier le plugin après installation.'
        [ "$result" -eq 0 ] && [ "$installed" = true ] && [ "$enabled" = true ] || abort_installation 'Installation du plugin impossible. Relancez cette commande.'
    fi
fi
if verify; then printf '%s\n' 'Installation complète'; exit 0; fi
[ "$installed" = true ] || fail 'Nestor doit être installé avant ce contrôle.'
if [ "$check_only" = true ] || [ "$no_login" = true ] || [ "$terminal" = false ]; then incomplete; fi
printf '%s' 'Ouvrir la connexion Nestor dans le navigateur ? (o/N) : ' >&3
IFS= read -r answer <&3 || incomplete
case "$answer" in o|O|oui|y|Y|yes) ;; *) incomplete ;; esac
login || incomplete
if verify; then printf '%s\n' 'Installation complète'; exit 0; fi
incomplete
