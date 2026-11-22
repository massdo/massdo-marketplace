# Result lines go to stdout, and their colors are decided once

The wizard's result lines go to stdout. `tint` mostly runs inside `$(...)`, where stdout is a pipe, so it cannot tell by itself whether the output is a terminal. Whether to color the marks is decided once, at the top level, into `colors`; `tint` reads that variable.

The marks are colored only when stdout is a terminal, except in `choose_clients`, which sets `local colors=true` because the menu is drawn on the terminal whatever stdout is.

Code:

- `install.sh`: `colors`, `tint`
