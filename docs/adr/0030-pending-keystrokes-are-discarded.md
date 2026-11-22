# Pending keystrokes are discarded before the wizard asks

A user may type while the apps are being checked or before a sign-in starts. Those keystrokes would otherwise reach the menu or the sign-in as answers. `flush_terminal_input` reads and drops the pending terminal input before the menu is shown and before the sign-in.

Keystrokes typed before the menu or the sign-in are not taken as answers.

Code:

- `install.sh`: `flush_terminal_input`, `login`
- `uninstall.sh`: `flush_terminal_input`
