# Browser apps are set up from their own page, with a guide

claude.ai and ChatGPT have no command line: Nestor is added from their own page. The installer cannot read their state and cannot check what the browser did. For these apps the wizard shows the steps, offers to open the page, and ends the app with a guided result. The menu always offers them, unchecked.

In `install.sh` the summary shows the guided result.

Code:

- `install.sh`: `claude_ai_page`, `chatgpt_page`, `client_guided`, `choose_clients`, `guide_client`
- `install.ps1`: `$claudeAiPage`, `$chatGptPage`, `Show-Guide` and the app prompt
