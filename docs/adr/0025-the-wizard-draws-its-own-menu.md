# The wizard draws its own menu instead of using gum choose

`gum choose` cannot check an app with Enter and stay open, and starting it again after each Enter made the menu blink. `install.sh` draws the menu itself, on the terminal whatever stdout is. Each key redraws the same lines in place, with line wrapping off so that a narrow terminal clips them instead of shifting the redraw. Between keys the cursor waits on the first line, so closing the menu erases it from there. Enter on an app checks or unchecks it; Enter on the last line starts the setup of the checked apps.

`menu_restore` runs on each way out of the menu and in `cleanup`; it erases the menu and restores wrapping, the cursor and the terminal settings.

Code:

- `install.sh`: `menu_restore`, `choose_clients`
