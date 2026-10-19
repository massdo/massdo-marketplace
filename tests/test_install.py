"""Exercise the installer with isolated CLI doubles, never real accounts."""
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = os.environ.get('NESTOR_TEST_INSTALLER') == 'powershell'


@unittest.skipIf(os.name == 'nt' and not POWERSHELL, 'Bash is tested on macOS, Linux and WSL')
class Installer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nestor installer test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.state = self.root / 'state.json'
        self.log = self.root / 'calls.jsonl'
        fixture = (ROOT / 'tests/fixtures/installer_client.py').read_text()
        if os.name == 'nt':
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            subprocess.run([str(compiler), '/nologo', '/target:exe', '/out:' + str(self.bin / 'codex.exe'),
                            str(ROOT / 'tests/fixtures/installer_client_launcher.cs')], check=True,
                           capture_output=True)
            shutil.copy2(self.bin / 'codex.exe', self.bin / 'claude.exe')
        else:
            for client in ('codex', 'claude'):
                path = self.bin / client
                path.write_text('#!/usr/bin/env python3\n' + fixture.split('\n', 1)[1])
                path.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'NESTOR_TEST_STATE': str(self.state), 'NESTOR_TEST_LOG': str(self.log),
                    'NESTOR_TEST_PYTHON': sys.executable, 'PYTHONUTF8': '1',
                    'NESTOR_TEST_FIXTURE': str(ROOT / 'tests/fixtures/installer_client.py')}

    def command(self, client, options):
        if POWERSHELL:
            names = {'--check': '-Check', '--no-login': '-NoLogin'}
            result = [os.environ.get('NESTOR_TEST_PWSH', 'pwsh'), '-NoProfile', '-File',
                      str(ROOT / 'install.ps1')]
            if client is not None:
                result.extend(['-Client', client])
            return result + [names.get(option, option) for option in options]
        result = ['/bin/bash', str(ROOT / 'install.sh')]
        if client is not None:
            result.extend(['--client', client])
        return result + list(options)

    def run_installer(self, client='codex', state=None, options=('--check',)):
        self.state.write_text(json.dumps(state or {}))
        return subprocess.run(self.command(client, options),
                              env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
                              encoding='utf-8', errors='replace', timeout=60, start_new_session=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def assert_no_mutations(self):
        self.assertFalse(any(any(word in call for word in ('login', 'add', 'install', 'enable'))
                             and '--help' not in call for call in self.calls()), self.calls())

    def run_interactive(self, command, responses):
        import pty
        pid, terminal = pty.fork()
        if pid == 0:
            os.execvpe(command[0], command, {**self.env, 'TERM': 'dumb'})
        output = bytearray()
        deadline = time.monotonic() + 60
        pending = list(responses)
        try:
            while True:
                if time.monotonic() >= deadline:
                    os.killpg(pid, 9)
                    self.fail('Interactive scenario timed out: ' + output.decode(errors='replace'))
                ready, _, _ = select.select([terminal], [], [], 1)
                if not ready:
                    continue
                try:
                    part = os.read(terminal, 8192)
                except OSError:
                    break
                if not part:
                    break
                output.extend(part)
                if pending and pending[0][0] in output.decode(errors='replace'):
                    _, answer = pending.pop(0)
                    os.write(terminal, (answer + '\n').encode())
        finally:
            os.close(terminal)
            _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status), output.decode(errors='replace')

    def test_connected_clients_succeed_without_login_or_configuration_changes(self):
        for client in ('codex', 'claude'):
            with self.subTest(client=client):
                result = self.run_installer(client)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Installation complète', result.stdout)
        self.assert_no_mutations()

    def test_failed_checks_never_report_complete(self):
        cases = [{'connected': False}, {'disabled_skill': True}, {'enabled': False},
                 {'url': 'https://other.example/mcp'}, {'invalid_json': True},
                 {'installed': False}, {'network_failure': True}, {'missing_server': True}]
        for client in ('codex', 'claude'):
            for state in cases:
                with self.subTest(client=client, state=state):
                    result = self.run_installer(client, state)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn('Installation complète', result.stdout)
        self.assert_no_mutations()

    def test_codex_requires_discovered_tools_and_no_discovery_error(self):
        for state in ({'missing_tools': True}, {'tools_error': 'offline'}):
            result = self.run_installer(state=state)
            self.assertEqual(result.returncode, 2)
            self.assertIn('codex mcp login nestor', result.stdout)

    def test_invalid_arguments_fail(self):
        result = self.run_installer(client='unknown')
        self.assertEqual(result.returncode, 1)

    def test_fresh_install_without_terminal_keeps_plugin_and_defers_oauth(self):
        for client in ('codex', 'claude'):
            result = self.run_installer(client, {'installed': False, 'marketplace': False,
                                        'connected': False, 'other_settings': {'keep': 42}}, ())
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('Plugin installé — connexion Nestor à terminer', result.stdout)
            state = json.loads(self.state.read_text())
            self.assertTrue(state['installed'])
            self.assertTrue(state['marketplace'])
            self.assertEqual(state['other_settings'], {'keep': 42})
        self.assertFalse(any('login' in call and '--help' not in call for call in self.calls()))

    def test_rerun_does_not_reinstall_or_change_existing_configuration(self):
        state = {'installed': True, 'marketplace': True, 'connected': True, 'other_settings': ['keep']}
        for client in ('codex', 'claude'):
            result = self.run_installer(client, state, ())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.state.read_text()), state)
        self.assert_no_mutations()

    def test_disabled_plugin_is_enabled_without_changing_other_settings(self):
        for client in ('codex', 'claude'):
            result = self.run_installer(client, {'enabled': False, 'other_settings': ['keep']}, ())
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads(self.state.read_text())
            self.assertTrue(state['enabled'])
            self.assertEqual(state['other_settings'], ['keep'])

    def test_collisions_stop_before_any_mutation(self):
        cases = [{'marketplace_repo': 'other/repository'}, {'plugin_marketplace': 'foreign'},
                 {'installed': False, 'manual_server': True}, {'url': 'https://other.example/mcp'}]
        for client in ('codex', 'claude'):
            for state in cases:
                with self.subTest(client=client, state=state):
                    result = self.run_installer(client, state, ())
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Collision', result.stderr)
                    self.assertNotIn('Installation complète', result.stdout)
                    self.assertEqual(json.loads(self.state.read_text()), state)
        self.assert_no_mutations()

    def test_no_terminal_requires_explicit_client(self):
        result = self.run_installer(None, options=())
        self.assertNotEqual(result.returncode, 0)
        self.assert_no_mutations()

    def test_missing_client_fails_without_mutation(self):
        for path in self.bin.iterdir():
            path.unlink()
        self.env['PATH'] = str(self.bin)
        result = self.run_installer(options=())
        self.assertNotEqual(result.returncode, 0)
        self.assert_no_mutations()

    def test_incompatible_client_fails_before_mutation(self):
        result = self.run_installer(state={'incompatible': True}, options=())
        self.assertNotEqual(result.returncode, 0)
        self.assert_no_mutations()

    def test_missing_install_capability_stops_before_adding_marketplace(self):
        for client in ('codex', 'claude'):
            command = 'plugin add' if client == 'codex' else 'plugin install'
            state = {'installed': False, 'marketplace': False, 'missing_capability': command}
            result = self.run_installer(client, state, ())
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(self.state.read_text()), state)
        self.assert_no_mutations()

    def test_failed_install_can_be_resumed_without_duplicate(self):
        for client in ('codex', 'claude'):
            result = self.run_installer(client, {'installed': False, 'partial_install_failure': True,
                                               'connected': False}, ())
            self.assertEqual(result.returncode, 2, result.stderr)
            state = json.loads(self.state.read_text())
            self.assertTrue(state['installed'])
            state.update(connected=True, partial_install_failure=False)
            self.log.write_text('')
            result = self.run_installer(client, state, ())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_no_mutations()

    def test_native_install_auth_is_reused_without_second_login(self):
        for client in ('codex', 'claude'):
            result = self.run_installer(client, {'installed': False, 'connected': False, 'auto_auth': True}, ())
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any('login' in call and '--help' not in call for call in self.calls()))

    def test_colored_native_output_is_accepted(self):
        result = self.run_installer('claude', {'color': True})
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(POWERSHELL, 'PowerShell has a built-in JSON parser')
    def test_downloaded_json_parser_with_wrong_checksum_is_never_executed(self):
        utilities = self.root / 'utilities'
        utilities.mkdir()
        for name in ('uname', 'mktemp', 'rm', 'sha256sum', 'shasum'):
            source = shutil.which(name)
            if source:
                (utilities / name).symlink_to(source)
        (utilities / 'codex').symlink_to(self.bin / 'codex')
        curl = utilities / 'curl'
        curl.write_text('#!/bin/bash\nwhile [ "$#" -gt 0 ]; do\n'
                        'if [ "$1" = -o ]; then printf invalid > "$2"; exit 0; fi\nshift\ndone\nexit 1\n')
        curl.chmod(0o755)
        self.env['PATH'] = str(utilities)
        temporary = self.root / 'temporary'
        temporary.mkdir()
        self.env['TMPDIR'] = str(temporary)
        result = self.run_installer()
        self.assertEqual(result.returncode, 1)
        self.assertIn('SHA-256', result.stderr)
        self.assertEqual(list(temporary.iterdir()), [])
        self.assertEqual(self.calls(), [])

    @unittest.skipIf(os.name == 'nt', 'Interactive terminal scenarios run on macOS and Linux')
    def test_oauth_acceptance_refusal_and_report_use_one_native_login(self):
        for client in ('codex', 'claude'):
            for refusal, answer, expected in ((False, 'o', 0), (True, 'o', 2), (False, 'n', 2)):
                with self.subTest(client=client, refusal=refusal, answer=answer):
                    self.log.write_text('')
                    self.state.write_text(json.dumps({'installed': False, 'connected': False,
                                                      'refuse_oauth': refusal}))
                    code, output = self.run_interactive(self.command(client, ()), [('navigateur', answer)])
                    self.assertEqual(code, expected, output)
                    logins = [call for call in self.calls() if 'login' in call and '--help' not in call]
                    self.assertEqual(len(logins), 1 if answer == 'o' else 0)
                    if expected:
                        self.assertIn('Plugin installé — connexion Nestor à terminer', output)

    @unittest.skipIf(os.name == 'nt', 'Interactive terminal scenarios run on macOS and Linux')
    def test_client_choice_and_piped_script_keep_terminal_input_separate(self):
        self.state.write_text(json.dumps({'installed': False, 'connected': False}))
        if POWERSHELL:
            command = self.command(None, ())
        else:
            command = ['/bin/bash', '-c', 'cat "$1" | /bin/bash -s --', 'installer', str(ROOT / 'install.sh')]
        code, output = self.run_interactive(command, [('Client à utiliser', 'claude'), ('navigateur', 'o')])
        self.assertEqual(code, 0, output)
        self.assertIn('Installation complète', output)


if __name__ == '__main__':
    unittest.main()
