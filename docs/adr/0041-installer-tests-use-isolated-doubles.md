# Installer tests use isolated CLI doubles, never real accounts

The installer drives real client CLIs and opens browser pages. A test must not touch an installed app, an account or a browser. The tests run the installer against offline doubles of the clients. The state and the call log of a double belong to one test directory. In the Bash tests, `open` and `xdg-open` are doubles that only record the call. `test_menu_offers_the_browser_apps_without_any_installed_app` removes the client doubles and restricts `PATH` to the remaining doubles and the system tools, so no real app is found.

A test reads what the installer did from the call log of its own directory.

Code:

- `tests/test_install.py`: `setUp`, `test_menu_offers_the_browser_apps_without_any_installed_app`
- `tests/fixtures/installer_client.py`
