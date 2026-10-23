#!/bin/sh
# Builds the global shortcut that opens the next waiting agent, and starts it at login. macOS only.
# Usage: sh install.sh [character], the key that types `character` with ⌘; "@" by default
# (the top-left key on a French Mac). Run it again after an update of the plugin.
set -eu

char=${1:-@}
case "$char" in
    ?) ;;
    *) echo "Give one character, the key to press with ⌘." >&2; exit 1 ;;
esac
case "$char" in
    '&' | '<' | '>') echo "Pick another key: $char cannot go in the LaunchAgent." >&2; exit 1 ;;
esac

here=$(cd "$(dirname "$0")" && pwd)
dir="$HOME/.claude/agent-queue"
label=local.agent-queue.hotkey
plist="$HOME/Library/LaunchAgents/$label.plist"

mkdir -p "$dir" "$HOME/Library/LaunchAgents"
swiftc -O "$here/hotkey.swift" -o "$dir/hotkey"
cat >"$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$dir/hotkey</string>
    <string>$char</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
  <key>ThrottleInterval</key>
  <integer>30</integer>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>StandardErrorPath</key>
  <string>$dir/hotkey.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
echo "⌘$char now opens the next waiting agent. Log: $dir/hotkey.log"
