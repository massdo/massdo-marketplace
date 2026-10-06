"""Exercise historical Git evidence and the publisher's real HTTP boundary."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import publish_plugin_releases as publisher
from plugin_release_history import load_history


class PluginReleasePublication(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="marketplace-history-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "History fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.releases = [
            {"name": "nestor", "version": "0.7.10", "version_hash": "1043de0a13ba515a", "changelog": "Stable"},
            {"name": "nestor-beta", "version": "0.9.6", "version_hash": "82a6866cadd70f62", "changelog": "Beta"},
        ]
        self.write_releases()
        (self.root / "plugins/nestor/mcp.json").write_text(json.dumps({
            "mcpServers": {"nestor": {"url": "https://example.invalid/mcp"}}}))
        self.write_history([])
        self.commit()
        self.base = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.history = [{key: release[key] for key in ("name", "version", "version_hash")}
                        | {"commit": self.base,
                           "validation_run": "https://github.com/massdo/massdo-marketplace/actions/runs/1"}
                        for release in self.releases]
        self.write_history(self.history)
        self.addCleanup(patch.stopall)
        patch.multiple(publisher, ROOT=self.root, RELEASE_NAMES=("nestor", "nestor-beta")).start()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env, text=True).strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "Published fixture")

    def write_history(self, entries):
        (self.root / "plugin-release-history.json").write_text(json.dumps(entries))

    def write_releases(self):
        for release in self.releases:
            path = self.root / "plugins" / release["name"] / "plugin-release.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({key: value for key, value in release.items() if key != "name"}))

    def test_payload_contains_all_history_without_evidence_or_changelogs(self):
        self.releases[1].update(version="0.10.0", version_hash="77cfad66a8f3745e")
        self.write_releases()
        payload = json.loads(publisher.release_payload())
        self.assertEqual(set(payload), {"releases", "history"})
        self.assertEqual(payload["releases"], self.releases)
        self.assertEqual(payload["history"], [
            {key: entry[key] for key in ("name", "version", "version_hash")} for entry in self.history])
        self.assertEqual(json.loads(publisher.release_payload()), payload)

    def test_independent_releases_are_not_discovered_but_keep_published_history(self):
        independent = {"name": "massdo-skills", "version": "0.11.2",
                       "version_hash": "0a6bcd189636a1d9", "changelog": "Legacy release"}
        self.releases.append(independent)
        self.write_releases()
        self.commit()
        baseline = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", baseline)
        self.history.append({key: independent[key] for key in ("name", "version", "version_hash")}
                            | {"commit": baseline,
                               "validation_run": "https://github.com/massdo/massdo-marketplace/actions/runs/2"})
        self.write_history(self.history)
        independent.pop("version_hash")
        scripts = self.root / "scripts"
        scripts.mkdir()
        for name in ("publish_plugin_releases.py", "plugin_release_history.py"):
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        for version in ("0.11.3", "0.11.4"):
            with self.subTest(version=version):
                independent.update(version=version, changelog="Standalone skills " + version)
                self.write_releases()
                # Import in the fixture to exercise real discovery, not the patched names.
                payload = json.loads(subprocess.check_output(
                    [sys.executable, "-c", "import sys; sys.path.insert(0, 'scripts'); "
                     "import publish_plugin_releases as p; print(p.release_payload().decode())"],
                    cwd=self.root, env=self.env, text=True))
                self.assertEqual(payload["releases"], self.releases[:2])
                self.assertEqual(payload["history"], [
                    {key: entry[key] for key in ("name", "version", "version_hash")}
                    for entry in self.history])
                load_history(self.root, self.releases, baseline=baseline)
                self.commit()
                baseline = self.git("rev-parse", "HEAD")
                self.git("update-ref", "refs/remotes/origin/main", baseline)
        self.write_history(self.history[:-1])
        with self.assertRaisesRegex(ValueError, "preserve previous associations"):
            load_history(self.root, self.releases, baseline=baseline)

    def test_invalid_evidence_stops_publication_before_http(self):
        for field, value, message in (
                ("version_hash", "ffffffffffffffff", "disagrees with published source"),
                ("commit", "f" * 40, "not a published main revision"),
                ("validation_run", "https://example.invalid/run/1", "validation run URL")):
            with self.subTest(field=field), patch.dict(os.environ, {publisher.SECRET_NAME: "fixture-secret"}):
                invalid = [dict(entry) for entry in self.history]
                invalid[0][field] = value
                self.write_history(invalid)
                with patch.object(publisher, "urlopen") as request:
                    with self.assertRaisesRegex(ValueError, message):
                        publisher.publish()
                    request.assert_not_called()

    def test_unpublished_work_branch_is_not_historical_evidence(self):
        self.git("switch", "-qc", "feature")
        self.releases[1].update(version="0.10.0", version_hash="77cfad66a8f3745e")
        self.write_releases()
        self.commit()
        self.history[1].update(version="0.10.0", version_hash="77cfad66a8f3745e",
                               commit=self.git("rev-parse", "HEAD"))
        self.write_history(self.history)
        with self.assertRaisesRegex(ValueError, "not a published main revision"):
            publisher.release_payload()

    def test_numeric_version_and_hash_collisions_are_refused(self):
        for replacement, message in (
                ({"version": "0.07.10", "version_hash": "ffffffffffffffff"}, "conflicting hashes"),
                ({"version": "0.7.11", "version_hash": self.releases[1]["version_hash"]}, "reuses hash")):
            with self.subTest(replacement=replacement):
                releases = [dict(entry) for entry in self.releases]
                releases[0].update(replacement)
                with self.assertRaisesRegex(ValueError, message):
                    load_history(self.root, releases)

    def test_duplicate_and_missing_history_are_refused(self):
        self.write_history(self.history + [self.history[0]])
        with self.assertRaisesRegex(ValueError, "repeats an association"):
            publisher.release_payload()
        (self.root / "plugin-release-history.json").unlink()
        with self.assertRaises(FileNotFoundError):
            publisher.release_payload()

    def test_missing_main_ref_does_not_trust_the_current_checkout(self):
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        with self.assertRaisesRegex(ValueError, "cannot read Git evidence"):
            publisher.release_payload()

    def test_endpoint_keeps_the_existing_server_route(self):
        self.assertEqual(publisher.release_endpoint(), "https://example.invalid/internal/plugin-releases")

    def test_previous_associations_cannot_be_deleted(self):
        self.commit()
        baseline = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", baseline)
        self.write_history(self.history[1:])
        with self.assertRaisesRegex(ValueError, "preserve previous associations"):
            publisher.release_payload()

    def test_previous_current_release_must_be_retained_on_bump(self):
        self.write_history([])
        self.releases[1].update(version="0.10.0", version_hash="77cfad66a8f3745e")
        self.write_releases()
        with self.assertRaisesRegex(ValueError, "retain the previous release"):
            publisher.release_payload()

    def test_payload_size_limit_is_checked_before_http(self):
        self.releases[0]["changelog"] = "x" * 65_536
        self.write_releases()
        with self.assertRaisesRegex(ValueError, "exceeds 65536"):
            publisher.release_payload()

    @contextmanager
    def endpoint(self, status=200, body=b'{"status":"ok","count":2}'):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.path, self.headers["Authorization"],
                                 json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(publisher, "release_endpoint",
                              return_value=f"http://127.0.0.1:{server.server_port}/internal/plugin-releases"), \
                    patch.dict(os.environ, {publisher.SECRET_NAME: "fixture-secret"}):
                yield requests
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_authenticated_publication_sends_history_on_every_call(self):
        with self.endpoint() as requests:
            publisher.publish()
            publisher.publish()
        self.assertEqual(len(requests), 2)
        for path, authorization, payload in requests:
            self.assertEqual(path, "/internal/plugin-releases")
            self.assertEqual(authorization, "Bearer fixture-secret")
            self.assertEqual(len(payload["history"]), 2)
        self.assertEqual(requests[0], requests[1])

    def test_http_refusal_and_invalid_confirmations_fail(self):
        for status, body, message in ((409, b'{}', "HTTP 409"),
                                      (200, b'not JSON', "invalid JSON"),
                                      (200, b'{"status":"ok","count":1}', "expected")):
            with self.subTest(status=status, body=body), self.endpoint(status, body):
                with self.assertRaisesRegex(SystemExit, message):
                    publisher.publish()
