#!/usr/bin/env python3

"""Publish the current Nestor release documents to the journal server."""

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
RELEASE_NAMES = ("nestor", "nestor-beta")
SECRET_NAME = "JOURNAL_MCP_PLUGIN_RELEASE_SECRET"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def release_endpoint() -> str:
    manifest = read_json(ROOT / "plugins" / "nestor" / "mcp.json")
    mcp_url = manifest["mcpServers"]["nestor"]["url"]
    parsed = urlsplit(mcp_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/internal/plugin-releases", "", ""))


def release_payload() -> bytes:
    releases = []
    for name in RELEASE_NAMES:
        release = read_json(ROOT / "plugins" / name / "plugin-release.json")
        releases.append({"name": name, **release})
    return json.dumps({"releases": releases}, separators=(",", ":")).encode()


def publish() -> None:
    secret = os.environ.get(SECRET_NAME, "").strip()
    if not secret:
        raise SystemExit(f"{SECRET_NAME} is required")

    request = Request(
        release_endpoint(),
        data=release_payload(),
        method="POST",
        headers={
            "Authorization": "Bearer " + secret,
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            body = response.read()
    except HTTPError as error:
        raise SystemExit(f"plugin release notification failed with HTTP {error.code}") from error
    except URLError as error:
        raise SystemExit(f"plugin release notification failed: {error.reason}") from error

    if status != 200:
        raise SystemExit(f"plugin release notification returned HTTP {status}, expected 200")
    try:
        confirmation = json.loads(body)
    except json.JSONDecodeError as error:
        raise SystemExit("plugin release notification returned invalid JSON") from error

    expected = {"status": "ok", "count": len(RELEASE_NAMES)}
    if confirmation != expected:
        raise SystemExit(
            f"plugin release notification returned {confirmation!r}, expected {expected!r}"
        )

    print(f"Published {len(RELEASE_NAMES)} plugin releases.")


if __name__ == "__main__":
    try:
        publish()
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"plugin release notification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
