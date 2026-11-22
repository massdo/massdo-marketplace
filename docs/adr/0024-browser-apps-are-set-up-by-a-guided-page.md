# Browser apps are set up from their own page, with a guide

claude.ai and ChatGPT have no command line: Nestor is added from their own page. The installer cannot read their state and cannot check what the browser did. For these apps the wizard shows the steps and offers to open the page. The menu always offers them, unchecked.

In `install.sh` the app ends with a guided result, which the summary shows. In `install.ps1`, `Show-Guide` ends with exit code 0.

Code:

- `install.sh`: `claude_ai_page`, `chatgpt_page`, `client_guided`, `choose_clients`, `guide_client`
- `install.ps1`: `$claudeAiPage`, `$chatGptPage`, `Show-Guide` and the app prompt
