# Cursor Agent's sign-in output is relayed without the authorization code

Cursor Agent echoes the first characters of the OAuth authorization code it received on stdout. The wizard relays the sign-in output to the terminal without that line. A flag file marks the end of the relay, so the wizard's next line waits for it.

That line never reaches the terminal. The test double prints the same line as Cursor Agent, so the tests exercise the filter.

Code:

- `install.sh`: `relay_login_output`, `relay_login_wait`
- `tests/fixtures/installer_client.py`: the `mcp login` branch
