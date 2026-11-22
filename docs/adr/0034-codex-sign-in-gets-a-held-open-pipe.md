# The Codex sign-in reads from a pipe held open

During `mcp login`, Codex also reads a pasted callback URL from a terminal, with hidden input, and cancels the sign-in on a bare Enter. The wizard gives Codex a pipe held open instead of the terminal: there is nothing to read, and the browser callback alone completes the sign-in. Keystrokes typed before the sign-in are discarded first.

A stray Enter cannot cancel the sign-in. The test double reads a terminal the same way and leaves any other input unread.

Code:

- `install.sh`: `login`
- `tests/fixtures/installer_client.py`: the `mcp login` branch
