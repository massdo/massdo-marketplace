#!/usr/bin/env python3

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "nestor-journal-assistant"
SKILL = PLUGIN / "skills" / "nestor-journal" / "SKILL.md"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


codex_manifest = read_json(PLUGIN / ".codex-plugin" / "plugin.json")
claude_manifest = read_json(PLUGIN / ".claude-plugin" / "plugin.json")
cursor_manifest = read_json(PLUGIN / ".cursor-plugin" / "plugin.json")
mcp = read_json(PLUGIN / ".mcp.json")
cursor_mcp = read_json(PLUGIN / "mcp.json")
codex_marketplace = read_json(ROOT / ".agents" / "plugins" / "marketplace.json")
claude_marketplace = read_json(ROOT / ".claude-plugin" / "marketplace.json")
cursor_marketplace = read_json(ROOT / ".cursor-plugin" / "marketplace.json")

MCP_URL = "https://journal.mcp-marketplace.org/mcp"

assert codex_manifest["name"] == "nestor-journal-assistant"
assert codex_manifest["skills"] == "./skills/"
assert codex_manifest["mcpServers"] == "./.mcp.json"
assert claude_manifest["name"] == "nestor-journal-assistant"
assert "version" not in claude_manifest
assert cursor_manifest["name"] == "nestor-journal-assistant"
assert cursor_manifest["mcpServers"] == "./mcp.json"
assert mcp["mcpServers"]["nestor-journal-assistant"]["url"] == MCP_URL
assert cursor_mcp["mcpServers"]["nestor-journal-assistant"]["url"] == MCP_URL
assert cursor_mcp["mcpServers"]["nestor-journal-assistant"]["type"] == "http"
assert codex_marketplace["plugins"][0]["source"]["path"] == (
    "./plugins/nestor-journal-assistant"
)
assert claude_marketplace["plugins"][0]["source"] == (
    "./plugins/nestor-journal-assistant"
)
assert cursor_marketplace["plugins"][0]["source"] == (
    "./plugins/nestor-journal-assistant"
)

skill_files = list(ROOT.rglob("SKILL.md"))
assert skill_files == [SKILL], f"Expected one canonical SKILL.md, found {skill_files}"

text = SKILL.read_text(encoding="utf-8")
frontmatter = re.match(r"^---\n(?P<body>.*?)\n---\n", text, re.DOTALL)
assert frontmatter is not None, "SKILL.md frontmatter is missing"
metadata = frontmatter.group("body")
assert re.search(r"^name: nestor-journal$", metadata, re.MULTILINE)
assert re.search(r"^description: .+", metadata, re.MULTILINE)

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    content = path.read_text(encoding="utf-8", errors="ignore")
    bearer_header = "Authorization:" + " Bearer"
    assert bearer_header not in content, f"Secret-like header in {path}"

print("Nestor plugin repository validation passed.")
