"""Exercise the installer with isolated CLI doubles, never real accounts."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Installer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nestor-installer-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.state = self.root / 'state.json'
        self.log = self.root / 'calls.jsonl'
        fixture = (ROOT / 'tests/fixtures/installer_client.py').read_text()
        for client in ('codex', 'claude'):
            path = self.bin / client
            path.write_text('#!' + sys.executable + '\n' + fixture.split('\n', 1)[1])
            path.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'NESTOR_TEST_STATE': str(self.state), 'NESTOR_TEST_LOG': str(self.log)}

    def run_installer(self, client='codex', state=None, options=('--check',)):
        self.state.write_text(json.dumps(state or {}))
        return subprocess.run(['/bin/bash', str(ROOT / 'install.sh'), '--client', client, *options],
                              env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=60, start_new_session=True)

    def test_connected_clients_succeed_without_login_or_configuration_changes(self):
        for client in ('codex', 'claude'):
            with self.subTest(client=client):
                result = self.run_installer(client)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Installation complète', result.stdout)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertFalse(any('login' in call or 'add' in call or 'install' in call for call in calls))

    def test_failed_checks_never_report_complete(self):
        cases = [{'connected': False}, {'disabled_skill': True}, {'enabled': False},
                 {'url': 'https://other.example/mcp'}, {'invalid_json': True},
                 {'installed': False}, {'network_failure': True}]
        for client in ('codex', 'claude'):
            for state in cases:
                with self.subTest(client=client, state=state):
                    result = self.run_installer(client, state)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn('Installation complète', result.stdout)

    def test_codex_requires_discovered_tools_and_no_discovery_error(self):
        for state in ({'missing_tools': True}, {'tools_error': 'offline'}):
            result = self.run_installer(state=state)
            self.assertEqual(result.returncode, 2)
            self.assertIn('codex mcp login nestor', result.stdout)

    def test_invalid_arguments_fail(self):
        result = self.run_installer(client='unknown')
        self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
