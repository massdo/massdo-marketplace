# Pages open with a detached system opener, and the URL stays on screen

The wizard opens a browser page for the guided apps. The user may close the terminal, or the wizard may end, before the page opens. Some systems have no opener. `open_page` uses the system opener when there is one and detaches it, so it outlives the terminal. The URL stays on screen either way.

The page still opens when the wizard ends or the window closes first, and a system without an opener still shows where to go.

Code:

- `install.sh`: `open_page`
