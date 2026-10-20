"""Exercise the installer with isolated CLI doubles, never real accounts."""
import json
import os
import re
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
        fixture = (ROOT / 'tests/fixtures/installer_client.py').read_text(encoding='utf-8')
        if os.name == 'nt':
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            subprocess.run([str(compiler), '/nologo', '/target:exe', '/out:' + str(self.bin / 'codex.exe'),
                            str(ROOT / 'tests/fixtures/installer_client_launcher.cs')], check=True,
                           capture_output=True)
            shutil.copy2(self.bin / 'codex.exe', self.bin / 'claude.exe')
        else:
            for client in ('codex', 'claude', 'cursor-agent'):
                path = self.bin / client
                path.write_text('#!/usr/bin/env python3\n' + fixture.split('\n', 1)[1])
                path.chmod(0o755)
            menu = (ROOT / 'tests/fixtures/gum.py').read_text(encoding='utf-8')
            (self.bin / 'gum').write_text('#!/usr/bin/env python3\n' + menu.split('\n', 1)[1])
            (self.bin / 'gum').chmod(0o755)
            git = self.bin / 'git'
            git.write_text('#!/usr/bin/env python3\n'
                           'import os, shutil, sys\n'
                           'from pathlib import Path\n'
                           'if sys.argv[1] != "clone": sys.exit(1)\n'
                           'source = Path(os.environ["NESTOR_TEST_REPO"]) / "plugins/nestor"\n'
                           'target = Path(sys.argv[-1]) / "plugins/nestor"\n'
                           'target.parent.mkdir(parents=True)\n'
                           'shutil.copytree(source, target)\n')
            git.chmod(0o755)
        home = self.root / 'home'
        home.mkdir()
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'HOME': str(home), 'NESTOR_TEST_REPO': str(ROOT),
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

    def run_uninstaller(self, client, state=None):
        if state is not None:
            self.state.write_text(json.dumps(state))
        return subprocess.run(['/bin/bash', str(ROOT / 'uninstall.sh'), '--client', client],
                              env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
                              encoding='utf-8', errors='replace', timeout=60, start_new_session=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def menu(self):
        return next(call for call in self.calls() if call[:2] == ['gum', 'choose'] and '--help' not in call)

    def assert_only_inventory_reads(self):
        self.assertTrue(all(call[0] == 'gum' or call[1:3] == ['plugin', 'list'] for call in self.calls()),
                        self.calls())

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
                messages = [call[2] for call in self.calls() if call[1] == 'rpc-input']
                self.assertFalse(any(message.startswith('\ufeff') for message in messages), messages)
                self.assertEqual(result.returncode, 0, result.stderr + repr(self.calls()))
                self.assertIn('Installation complete', result.stdout)
        self.assert_no_mutations()

    @unittest.skipIf(POWERSHELL, 'Cursor is supported by the Bash entry point')
    def test_cursor_install_check_and_collision(self):
        plugin = Path(self.env['HOME']) / '.cursor/plugins/local/nestor'
        missing = self.run_installer('cursor')
        self.assertEqual(missing.returncode, 1, missing.stderr)
        installed = self.run_installer('cursor', options=())
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertIn('Installation complete', installed.stdout)
        self.assertTrue((plugin / 'skills/nestor/SKILL.md').is_file())
        self.assertEqual(self.run_installer('cursor').returncode, 0)
        shutil.rmtree(plugin)
        plugin.mkdir()
        (plugin / 'foreign').write_text('keep')
        collision = self.run_installer('cursor', options=())
        self.assertEqual(collision.returncode, 1, collision.stderr)
        self.assertTrue((plugin / 'foreign').exists())

    @unittest.skipIf(POWERSHELL, 'Cursor is supported by the Bash entry point')
    def test_cursor_existing_server_collision_prevents_install(self):
        config = Path(self.env['HOME']) / '.cursor/mcp.json'
        config.parent.mkdir()
        config.write_text(json.dumps({'mcpServers': {'nestor': {'url': 'https://other.example/mcp'}}}))
        result = self.run_installer('cursor', options=())
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('Collision', result.stderr)
        self.assertFalse((config.parent / 'plugins/local/nestor').exists())

    @unittest.skipIf(POWERSHELL, 'Cursor is supported by the Bash entry point')
    def test_cursor_pending_auth_and_missing_tools(self):
        pending = self.run_installer('cursor', {'connected': False}, ())
        self.assertEqual(pending.returncode, 2, pending.stderr)
        self.assertIn('cursor-agent mcp login nestor', pending.stdout)
        missing = self.run_installer('cursor', {'missing_tools': True})
        self.assertEqual(missing.returncode, 1, missing.stderr)
        self.assertNotIn('Installation complete', missing.stdout)

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'Interactive Cursor setup runs on macOS and Linux')
    def test_cursor_interactive_login_completes(self):
        self.state.write_text(json.dumps({'connected': False}))
        code, output = self.run_interactive(self.command('cursor', ()), [('browser', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('Installation complete', output)
        self.assertEqual(len([call for call in self.calls() if call[1:4] == ['mcp', 'login', 'nestor']]),
                         1, self.calls())

    @unittest.skipIf(POWERSHELL, 'Grok Bot is supported by the Bash entry point')
    def test_grokbot_is_an_explicit_manual_handoff(self):
        result = self.run_installer('grokbot', options=())
        self.assertEqual(result.returncode, 2)
        self.assertIn('Connect apps', result.stdout)
        self.assertIn('https://journal.mcp-marketplace.org/mcp', result.stdout)
        self.assertNotIn('Installation complete', result.stdout)
        self.assertEqual(self.calls(), [])

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'Grok Bot detection uses the Bash wizard')
    def test_grokbot_app_is_detected_in_interactive_menu(self):
        app = Path(self.env['HOME']) / 'Applications/Grok Bot.app'
        app.mkdir(parents=True)
        code, output = self.run_interactive(self.command(None, ()), [('Where should Nestor be installed', 'grokbot')])
        self.assertEqual(code, 2, output)
        self.assertIn('Connect apps', output)
        self.assertIn('Grok Bot — manual steps in the app|grokbot', self.menu())
        self.assert_only_inventory_reads()

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_marks_installed_apps_and_preselects_the_missing_ones(self):
        app = Path(self.env['HOME']) / 'Applications/Grok Bot.app'
        app.mkdir(parents=True)
        self.state.write_text(json.dumps({'installed': True, 'connected': True}))
        code, output = self.run_interactive(self.command(None, ()), [('Where should Nestor be installed', '')])
        self.assertEqual(code, 0, output)
        self.assertIn('Nothing selected', output)
        menu = self.menu()
        self.assertIn('Codex — \x1b[32minstalled 0.9.1\x1b[0m|codex', menu)
        self.assertIn('Claude Code — \x1b[32minstalled 0.9.1\x1b[0m|claude', menu)
        self.assertIn('Cursor Agent — not installed|cursor', menu)
        self.assertIn('Grok Bot — manual steps in the app|grokbot', menu)
        self.assertIn('--selected=Cursor Agent — not installed', menu)
        self.assert_only_inventory_reads()

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_sets_up_every_selected_app(self):
        self.state.write_text(json.dumps({'installed': False, 'marketplace': False, 'connected': False}))
        code, output = self.run_interactive(self.command(None, ()),
                                            [('Where should Nestor be installed', 'codex,claude'), ('browser', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('--selected=Codex — not installed,Claude Code — not installed,Cursor Agent — not installed',
                      self.menu())
        self.assertGreaterEqual(output.count('Installation complete'), 2, output)
        self.assertIn('Summary', output)
        self.assertTrue(any(call[1:3] in (['plugin', 'add'], ['plugin', 'install']) for call in self.calls()),
                        self.calls())
        state = json.loads(self.state.read_text())
        self.assertTrue(state['installed'] and state['connected'])

    @unittest.skipIf(POWERSHELL, 'Several --client values are a Bash option')
    def test_several_clients_report_each_result_and_the_worst_exit_code(self):
        result = self.run_installer(None, {}, ('--client', 'codex', '--client', 'claude', '--check'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('Installation complete'), 4, result.stdout)
        self.assertIn('Summary', result.stdout)
        result = self.run_installer(None, {'connected': False}, ('--client', 'codex,claude', '--check'))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Codex: finish connecting your account', result.stdout)
        self.assertIn('Claude Code: finish connecting your account', result.stdout)
        result = self.run_installer(None, {'disabled_skill': True}, ('--client', 'codex', '--client', 'claude', '--check'))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn('Installation complete', result.stdout)
        self.assert_no_mutations()

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu tool is downloaded by the Bash wizard')
    def test_downloaded_menu_tool_with_wrong_checksum_is_never_executed(self):
        utilities = self.root / 'utilities'
        utilities.mkdir()
        for name in ('uname', 'mktemp', 'mkdir', 'rm', 'sha256sum', 'shasum', 'jq', 'env', 'python3'):
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
        code, output = self.run_interactive(self.command(None, ()), [])
        self.assertEqual(code, 1, output)
        self.assertIn('SHA-256', output)
        self.assertEqual(list(temporary.iterdir()), [])
        self.assertEqual(self.calls(), [])

    @unittest.skipIf(POWERSHELL, 'The uninstall wizard is the Bash entry point')
    def test_uninstall_removes_only_the_selected_native_plugin(self):
        for client in ('codex', 'claude'):
            with self.subTest(client=client):
                result = self.run_uninstaller(client, {'installed': True, 'connected': True,
                                                       'other_settings': ['keep']})
                self.assertEqual(result.returncode, 0, result.stderr)
                state = json.loads(self.state.read_text())
                self.assertFalse(state['installed'])
                self.assertEqual(state['other_settings'], ['keep'])
                self.assertTrue(state.get('marketplace', True))
                self.log.write_text('')
                again = self.run_uninstaller(client)
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertFalse(any('remove' in call or 'uninstall' in call for call in self.calls()))

    @unittest.skipIf(POWERSHELL, 'The uninstall wizard is the Bash entry point')
    def test_cursor_uninstall_keeps_foreign_plugin_and_removes_owned_copy(self):
        plugin = Path(self.env['HOME']) / '.cursor/plugins/local/nestor'
        plugin.mkdir(parents=True)
        (plugin / 'foreign').write_text('keep')
        refused = self.run_uninstaller('cursor')
        self.assertEqual(refused.returncode, 1)
        self.assertTrue((plugin / 'foreign').exists())
        shutil.rmtree(plugin)
        external = self.root / 'other-plugin'
        external.mkdir()
        plugin.symlink_to(external, target_is_directory=True)
        self.assertEqual(self.run_uninstaller('cursor').returncode, 1)
        self.assertTrue(external.exists())
        plugin.unlink()
        self.assertEqual(self.run_installer('cursor', options=()).returncode, 0)
        removed = self.run_uninstaller('cursor')
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(plugin.exists())

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'Interactive removal uses the Bash wizard')
    def test_uninstall_wizard_selects_cursor(self):
        self.state.write_text('{}')
        self.assertEqual(self.run_installer('cursor', options=()).returncode, 0)
        code, output = self.run_interactive(['/bin/bash', str(ROOT / 'uninstall.sh')],
                                            [('Remove Nestor from which app', 'cursor')])
        self.assertEqual(code, 0, output)
        self.assertIn('Nestor removed from Cursor', output)

    @unittest.skipIf(POWERSHELL, 'The uninstall wizard is the Bash entry point')
    def test_grokbot_uninstall_requires_cloud_account_action(self):
        result = self.run_uninstaller('grokbot')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Connect apps', result.stdout)
        self.assertEqual(self.calls(), [])

    def test_failed_checks_never_report_complete(self):
        cases = [{'connected': False}, {'disabled_skill': True}, {'enabled': False},
                 {'url': 'https://other.example/mcp'}, {'invalid_json': True},
                 {'installed': False}, {'network_failure': True}, {'missing_server': True}]
        for client in ('codex', 'claude'):
            for state in cases:
                with self.subTest(client=client, state=state):
                    result = self.run_installer(client, state)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn('Installation complete', result.stdout)
        self.assert_no_mutations()

    def test_codex_requires_discovered_tools_in_object_or_array(self):
        for as_array in (False, True):
            result = self.run_installer(state={'tools_array': as_array})
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.run_installer(state={'tools_array': as_array, 'missing_tools': True})
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertNotIn('codex mcp login nestor', result.stdout)

    def test_synced_plugin_is_not_a_collision_or_an_install_target(self):
        for options in (('--check',), ()):
            result = self.run_installer('claude', {'synced': True}, options)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_mutations()

    @unittest.skipUnless(POWERSHELL, 'The Windows entry point uses a child PowerShell process')
    def test_documented_powershell_command_preserves_parent_and_resume_message(self):
        block = re.search(r'```powershell\n(.*?)\n```', (ROOT / 'README.md').read_text(encoding='utf-8'), re.DOTALL).group(1)
        self.assertNotIn('scriptblock', block.lower())
        self.assertIn('-File $installerPath', block)
        shell = os.environ.get('NESTOR_TEST_PWSH', 'pwsh')
        prefix = """
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
function Invoke-WebRequest {
    param([switch]$UseBasicParsing, [string]$Uri, [string]$OutFile)
    Copy-Item -LiteralPath $env:NESTOR_TEST_SCRIPT -Destination $OutFile
}
"""
        if os.name != 'nt':
            prefix += "\nfunction powershell.exe { & $env:NESTOR_TEST_PWSH @args }\n"
        self.env.update(NESTOR_TEST_SCRIPT=str(ROOT / 'install.ps1'), NESTOR_TEST_PWSH=shell)
        for state, expected in (({}, 0), ({'connected': False}, 2), ({'disabled_skill': True}, 1)):
            with self.subTest(expected=expected):
                self.state.write_text(json.dumps(state))
                command = block.replace('-File $installerPath', '-File $installerPath -Client codex -Check')
                command += '\nWrite-Output ("PARENT_ALIVE:" + $LASTEXITCODE)\n'
                command += 'if (Test-Path -LiteralPath $installerPath) { throw "Temporary script remains" }\n'
                result = subprocess.run([shell, '-NoProfile', '-Command', prefix + command],
                                        env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
                                        encoding='utf-8', errors='replace', timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('PARENT_ALIVE:' + str(expected), result.stdout)
                if expected == 2:
                    self.assertIn('Nestor is installed — finish connecting your account', result.stdout)
        self.assert_no_mutations()

    def test_non_authentication_failures_never_offer_login(self):
        for client in ('codex', 'claude'):
            cases = [{'disabled_skill': True}, {'enabled': False}, {'missing_server': True}]
            if client == 'codex':
                cases.append({'auth_status': 'unknown'})
            for state in cases:
                with self.subTest(client=client, state=state):
                    result = self.run_installer(client, state)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertNotIn('mcp login', result.stdout)
                    self.assertNotIn('finish connecting your account', result.stdout)
                    self.assertTrue(result.stderr.strip())
        self.assert_no_mutations()

    def test_connection_failure_keeps_plugin_and_prints_retry_without_login(self):
        for client in ('codex', 'claude'):
            cases = [{'tools_error': 'offline'}]
            cases.append({'runtime_status': 'failed'} if client == 'codex' else {'offline': True})
            for failure in cases:
                for options in (('--check',), ()):
                    with self.subTest(client=client, failure=failure, options=options):
                        state = {**failure, 'installed': bool(options), 'marketplace': bool(options),
                                 'other_settings': ['keep']}
                        result = self.run_installer(client, state, options)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn('Nestor is installed — finish connecting your account', result.stdout,
                                      result.stderr + repr(self.calls()))
                        self.assertIn('Try again:', result.stdout)
                        self.assertIn('If you are asked to sign in afterward', result.stdout)
                        server = 'nestor' if client == 'codex' else 'plugin:nestor:nestor'
                        self.assertIn(client + ' mcp login ' + server, result.stdout)
                        self.assertTrue(result.stderr.strip())
                        saved = json.loads(self.state.read_text())
                        self.assertTrue(saved['installed'])
                        self.assertEqual(saved['other_settings'], ['keep'])
                        self.assertFalse(any('login' in call and '--help' not in call for call in self.calls()))
                        for key in failure:
                            saved.pop(key)
                        self.log.write_text('')
                        resumed = self.run_installer(client, saved, ())
                        self.assertEqual(resumed.returncode, 0, resumed.stderr)
                        self.assert_no_mutations()

    def test_native_command_failures_keep_bounded_stderr(self):
        native_error = 'omitted native header\n' + 'detail\n' * 14 + 'fatal: accès au dépôt refusé'
        for client in ('codex', 'claude'):
            commands = [
                (['plugin', 'marketplace', 'add', 'massdo/massdo-marketplace'],
                 {'installed': False, 'marketplace': False}, ()),
                (['plugin', 'add', 'nestor@massdo-marketplace', '--json'] if client == 'codex' else
                 ['plugin', 'install', 'nestor@massdo-marketplace', '--scope', 'user'],
                 {'installed': False}, ()),
                (['plugin', 'list', '--json'], {}, ('--check',)),
                (['mcp', 'get', 'nestor', '--json'] if client == 'codex' else
                 ['plugin', 'details', 'nestor@massdo-marketplace'], {}, ('--check',)),
            ]
            if client == 'codex':
                commands.append((['app-server', '--stdio'], {}, ('--check',)))
            for command, state, options in commands:
                with self.subTest(client=client, command=command):
                    result = self.run_installer(client, {**state, 'fail_command': command,
                                                        'native_error': native_error}, options)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn('fatal: accès au dépôt refusé', result.stderr)
                    self.assertNotIn('omitted native header', result.stderr)
                    self.assertNotIn('Installation complete', result.stdout)

    @unittest.skipUnless(POWERSHELL, 'PowerShell process-start errors use the global exception handler')
    def test_unstartable_client_reports_native_exception(self):
        binary = self.bin / ('codex.exe' if os.name == 'nt' else 'codex')
        binary.write_bytes(b'not a native executable\n')
        result = self.run_installer()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        prefix = 'Client check failed:'
        self.assertIn(prefix, result.stderr)
        self.assertTrue(result.stderr.split(prefix, 1)[1].strip())

    @unittest.skipIf(os.name == 'nt', 'Interactive terminal scenarios run on macOS and Linux')
    def test_verification_failure_in_a_terminal_does_not_prompt_for_oauth(self):
        for client in ('codex', 'claude'):
            for state, expected in (({'disabled_skill': True}, 1), ({'tools_error': 'offline'}, 2)):
                self.state.write_text(json.dumps(state))
                code, output = self.run_interactive(self.command(client, ()), [])
                self.assertEqual(code, expected, output)
                self.assertNotIn('browser', output)
                self.assert_no_mutations()
        self.assert_no_mutations()

    def test_invalid_arguments_fail(self):
        result = self.run_installer(client='unknown')
        self.assertEqual(result.returncode, 1)

    def test_fresh_install_without_terminal_keeps_plugin_and_defers_oauth(self):
        for client in ('codex', 'claude'):
            result = self.run_installer(client, {'installed': False, 'marketplace': False,
                                        'connected': False, 'other_settings': {'keep': 42}}, ())
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('Nestor is installed — finish connecting your account', result.stdout,
                          result.stderr + repr(self.calls()))
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
                    self.assertNotIn('Installation complete', result.stdout)
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
            self.assertEqual(result.returncode, 1, result.stderr)
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
            for refusal, answer, expected in ((False, 'y', 0), (True, 'y', 2), (False, 'n', 2)):
                with self.subTest(client=client, refusal=refusal, answer=answer):
                    self.log.write_text('')
                    self.state.write_text(json.dumps({'installed': False, 'connected': False,
                                                      'refuse_oauth': refusal}))
                    code, output = self.run_interactive(self.command(client, ()), [('browser', answer)])
                    self.assertEqual(code, expected, output)
                    logins = [call for call in self.calls() if 'login' in call and '--help' not in call]
                    self.assertEqual(len(logins), 1 if answer == 'y' else 0)
                    if expected:
                        self.assertIn('Nestor is installed — finish connecting your account', output)

    @unittest.skipIf(os.name == 'nt', 'Interactive terminal scenarios run on macOS and Linux')
    def test_client_choice_and_piped_script_keep_terminal_input_separate(self):
        self.state.write_text(json.dumps({'installed': False, 'connected': False}))
        if POWERSHELL:
            command = self.command(None, ())
        else:
            command = ['/bin/bash', '-c', 'cat "$1" | /bin/bash -s --', 'installer', str(ROOT / 'install.sh')]
        prompt = 'Choose your app' if POWERSHELL else 'Where should Nestor be installed'
        code, output = self.run_interactive(command, [(prompt, 'claude'), ('browser', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('Installation complete', output)


if __name__ == '__main__':
    unittest.main()
