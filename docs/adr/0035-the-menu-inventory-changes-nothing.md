# The menu inventory reads the apps without changing anything

The menu shows one line per app with what the app already has. `inventory` only reads. Collisions and unreadable inventories are reported there as a state, and again, in full, when the app is set up.

`test_menu_marks_installed_apps_and_preselects_the_missing_ones` asserts that leaving the menu made no client call other than the inventory reads. `uninstall.sh` builds its menu lines under the same rule.

Code:

- `install.sh`: `inventory`
- `uninstall.sh`: `inventory`
