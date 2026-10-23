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
# Keys sent to the setup menu; each answer is followed by Enter.
DOWN = '\x1b[B'
ESCAPE = '\x1b'


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
            # The browser apps offer to open a page: the opener only records the call.
            for opener in ('open', 'xdg-open'):
                double = self.bin / opener
                double.write_text('#!/usr/bin/env python3\n'
                                  'import json, os, sys\n'
                                  'with open(os.environ["NESTOR_TEST_LOG"], "a") as handle:\n'
                                  '    handle.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + "\\n")\n')
                double.chmod(0o755)
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
        config = Path(self.env['HOME']) / '.cursor/mcp.json'
        config.parent.mkdir()
        config.write_text(json.dumps({'mcpServers': {'other': {'url': 'https://other.example/mcp'}}}))
        missing = self.run_installer('cursor')
        self.assertEqual(missing.returncode, 1, missing.stderr)
        installed = self.run_installer('cursor', options=())
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertIn('Installation complete', installed.stdout)
        self.assertTrue((plugin / 'skills/nestor/SKILL.md').is_file())
        servers = json.loads(config.read_text())['mcpServers']
        self.assertEqual(servers['nestor'], {'type': 'http', 'url': 'https://journal.mcp-marketplace.org/mcp'})
        self.assertEqual(servers['other'], {'url': 'https://other.example/mcp'})
        self.assertTrue((plugin / '.massdo-mcp-server').is_file())
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
        code, output = self.run_interactive(self.command('cursor', ()), [('Open your browser', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('Installation complete', output)
        self.assertIn('MCP login successful', output)
        self.assertNotIn('authorization code', output)
        self.assertEqual(len([call for call in self.calls() if call[1:4] == ['mcp', 'login', 'nestor']]),
                         1, self.calls())

    @unittest.skipIf(POWERSHELL, 'The Bash wizard refuses unknown apps by name')
    def test_unsupported_app_name_is_refused_without_mutation(self):
        result = self.run_installer('grokbot', options=())
        self.assertEqual(result.returncode, 1)
        self.assertIn('Choose codex, claude, cursor, claude-ai or chatgpt.', result.stderr)
        self.assertEqual(self.calls(), [])
        result = self.run_uninstaller('grokbot', {})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_marks_installed_apps_and_preselects_the_missing_ones(self):
        self.state.write_text(json.dumps({'installed': True, 'connected': True}))
        prompt = 'Where should Nestor be installed'
        # Down twice and Enter unchecks Cursor Agent; Down three times and Enter
        # passes the browser apps and launches with nothing checked.
        code, output = self.run_interactive(self.command(None, ()),
                                            [(prompt, DOWN * 2), (prompt, DOWN * 3), ('Check at least one app', ESCAPE)])
        self.assertEqual(code, 1, output)
        self.assertIn('App selection was interrupted', output)
        for row in ('☐ \x1b[38;5;36m◉\x1b[0m Codex — \x1b[32minstalled 0.9.1\x1b[0m',
                    '☐ \x1b[38;5;173m✳\x1b[0m Claude Code — \x1b[32minstalled 0.9.1\x1b[0m',
                    '\x1b[38;5;117m☑\x1b[0m \x1b[38;5;33m⬢\x1b[0m Cursor Agent — not installed',
                    '☐ \x1b[38;5;209m✦\x1b[0m claude.ai — set up in your browser',
                    '☐ \x1b[38;5;78m◎\x1b[0m ChatGPT — set up in your browser',
                    '\x1b[1m▶ Launch install\x1b[0m'):
            self.assertIn(row, output)
        self.assertNotIn('grokbot', output)
        self.assertFalse(any(call[:2] == ['gum', 'choose'] and '--help' not in call for call in self.calls()),
                         self.calls())
        self.assert_only_inventory_reads()

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_checks_with_enter_keeps_the_cursor_and_launches_from_the_last_line(self):
        self.state.write_text(json.dumps({'installed': True, 'connected': True}))
        prompt = 'Where should Nestor be installed'
        # Down and Enter twice: check Claude Code, uncheck Cursor Agent. Then Down
        # three times and Enter: past the browser apps, launch from the last line.
        code, output = self.run_interactive(self.command(None, ()),
                                            [(prompt, DOWN), (prompt, DOWN), (prompt, DOWN * 3)])
        self.assertEqual(code, 0, output)
        self.assertIn('Open a new conversation in Claude Code and type: Show my tasks.', output)
        self.assertFalse((self.root / 'home/.cursor/plugins/local/nestor').exists())

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_sets_up_every_selected_app(self):
        self.state.write_text(json.dumps({'installed': False, 'marketplace': False, 'connected': False}))
        prompt = 'Where should Nestor be installed'
        code, output = self.run_interactive(self.command(None, ()),
                                            [(prompt, DOWN * 2), (prompt, DOWN * 3), ('Open your browser', 'y')])
        self.assertEqual(code, 0, output)
        for row in ('\x1b[38;5;36m◉\x1b[0m Codex — not installed', '\x1b[38;5;173m✳\x1b[0m Claude Code — not installed',
                    '\x1b[38;5;33m⬢\x1b[0m Cursor Agent — not installed'):
            self.assertIn('\x1b[38;5;117m☑\x1b[0m ' + row, output)
        self.assertIn('Installation complete', output)
        self.assertIn('\x1b[38;5;36m◉\x1b[0m Codex — \x1b[32m✔ installed and connected\x1b[0m', output)
        self.assertIn('\x1b[38;5;173m✳\x1b[0m Claude Code — \x1b[32m✔ installed and connected\x1b[0m', output)
        self.assertFalse((self.root / 'home/.cursor/plugins/local/nestor').exists())
        self.assertIn('Summary', output)
        self.assertTrue(any(call[1:3] in (['plugin', 'add'], ['plugin', 'install']) for call in self.calls()),
                        self.calls())
        state = json.loads(self.state.read_text())
        self.assertTrue(state['installed'] and state['connected'])

    @unittest.skipIf(POWERSHELL, 'Several --client values are a Bash option')
    def test_several_clients_report_each_result_and_the_worst_exit_code(self):
        result = self.run_installer(None, {}, ('--client', 'codex', '--client', 'claude', '--check'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('Installation complete'), 1, result.stdout)
        self.assertEqual(result.stdout.count('Nestor is installed and connected to your account'), 2, result.stdout)
        self.assertIn('◉ Codex — ✔ installed and connected', result.stdout)
        self.assertIn('✳ Claude Code — ✔ installed and connected', result.stdout)
        self.assertNotIn('\x1b[', result.stdout)
        self.assertIn('Open a new conversation in Codex or Claude Code and type: Show my tasks.', result.stdout)
        self.assertIn('Summary', result.stdout)
        result = self.run_installer(None, {'connected': False}, ('--client', 'codex,claude', '--check'))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Codex — ⚠ finish connecting your account', result.stdout)
        self.assertIn('Claude Code — ⚠ finish connecting your account', result.stdout)
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
        config = Path(self.env['HOME']) / '.cursor/mcp.json'
        config.parent.mkdir(exist_ok=True)
        config.write_text(json.dumps({'mcpServers': {'other': {'url': 'https://other.example/mcp'}}}))
        self.assertEqual(self.run_installer('cursor', options=()).returncode, 0)
        self.assertIn('nestor', json.loads(config.read_text())['mcpServers'])
        removed = self.run_uninstaller('cursor')
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(plugin.exists())
        self.assertEqual(json.loads(config.read_text()), {'mcpServers': {'other': {'url': 'https://other.example/mcp'}}})

    @unittest.skipIf(POWERSHELL, 'Cursor is supported by the Bash entry point')
    def test_cursor_keeps_a_nestor_server_it_did_not_add(self):
        config = Path(self.env['HOME']) / '.cursor/mcp.json'
        config.parent.mkdir()
        existing = {'mcpServers': {'nestor': {'type': 'http', 'url': 'https://journal.mcp-marketplace.org/mcp'}}}
        config.write_text(json.dumps(existing))
        self.assertEqual(self.run_installer('cursor', options=()).returncode, 0)
        self.assertFalse((config.parent / 'plugins/local/nestor/.massdo-mcp-server').exists())
        self.assertEqual(self.run_uninstaller('cursor').returncode, 0)
        self.assertEqual(json.loads(config.read_text()), existing)

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'Interactive removal uses the Bash wizard')
    def test_uninstall_wizard_selects_cursor(self):
        self.state.write_text('{}')
        self.assertEqual(self.run_installer('cursor', options=()).returncode, 0)
        code, output = self.run_interactive(['/bin/bash', str(ROOT / 'uninstall.sh')],
                                            [('Remove Nestor from which app', 'cursor')])
        self.assertEqual(code, 0, output)
        self.assertIn('Nestor removed from Cursor', output)

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
                (['plugin', 'list', '--json', '-m', 'massdo-marketplace'] if client == 'codex' else
                 ['plugin', 'list', '--json'], {}, ('--check',)),
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

    def test_codex_inventory_names_the_marketplace(self):
        # Without a marketplace name, Codex also refreshes its remote plugin
        # catalog, which exceeded the inventory time budget on a cold cache.
        self.run_installer('codex')
        inventories = [call[1:] for call in self.calls()
                       if call[1:3] == ['plugin', 'list'] and '--help' not in call]
        self.assertTrue(inventories, self.calls())
        self.assertEqual(set(map(tuple, inventories)),
                         {('plugin', 'list', '--json', '-m', 'massdo-marketplace')})

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

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The Codex sign-in pipe is a Bash feature')
    def test_stray_enter_during_codex_sign_in_does_not_cancel_it(self):
        self.state.write_text(json.dumps({'installed': True, 'connected': False}))
        code, output = self.run_interactive(self.command('codex', ()), [('Open your browser', 'y'), ('Callback URL', '')])
        self.assertEqual(code, 0, output)
        self.assertIn('Nestor 0.9.1 is already installed.', output)
        self.assertIn('Nestor is not connected to your account yet.', output)
        self.assertIn('Opening your browser.', output)
        self.assertIn('Nestor is installed and connected to your account.', output)
        self.assertIn('Installation complete', output)
        self.assertIn('Open a new conversation in Codex and type: Show my tasks.', output)
        self.assertEqual(len([call for call in self.calls() if call[1:4] == ['mcp', 'login', 'nestor']]),
                         1, self.calls())

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'Interactive sign-in results are a Bash feature')
    def test_each_sign_in_outcome_is_explained(self):
        for state, answer, reason in (({'refuse_oauth': True}, 'y', 'The browser sign-in did not finish.'),
                                      ({}, 'n', 'Browser sign-in skipped.'),
                                      ({'stay_logged_out': True}, 'y', 'Codex still reports Nestor as not signed in.')):
            with self.subTest(reason=reason):
                self.log.write_text('')
                self.state.write_text(json.dumps({'installed': True, 'connected': False, **state}))
                code, output = self.run_interactive(self.command('codex', ()), [('browser', answer)])
                self.assertEqual(code, 2, output)
                self.assertIn(reason, output)
                self.assertIn('Nestor is installed — finish connecting your account', output)
                self.assertIn('To continue, run: codex mcp login nestor', output)
                self.assertIn('Nestor is installed but not connected to your account yet.', output)
                self.assertNotIn('Installation complete', output)

    @unittest.skipIf(os.name == 'nt', 'Interactive terminal scenarios run on macOS and Linux')
    def test_client_choice_and_piped_script_keep_terminal_input_separate(self):
        self.state.write_text(json.dumps({'installed': False, 'connected': False}))
        if POWERSHELL:
            command = self.command(None, ())
        else:
            command = ['/bin/bash', '-c', 'cat "$1" | /bin/bash -s --', 'installer', str(ROOT / 'install.sh')]
        if POWERSHELL:
            choices = [('Choose your app', 'claude')]
        else:
            prompt = 'Where should Nestor be installed'
            choices = [(prompt, ''), (prompt, DOWN * 2), (prompt, DOWN * 3)]
        code, output = self.run_interactive(command, choices + [('Open your browser', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('Installation complete', output)

    def test_browser_apps_show_their_steps_without_a_terminal_or_a_browser(self):
        pages = {'claude-ai': 'https://claude.ai/customize/connectors', 'chatgpt': 'https://chatgpt.com/plugins'}
        for client, page in pages.items():
            for options in ((), ('--check',), ('--no-login',)):
                with self.subTest(client=client, options=options):
                    result = self.run_installer(client, {}, options)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(page, result.stdout)
                    self.assertIn('https://journal.mcp-marketplace.org/mcp', result.stdout)
                    self.assertIn('Finish the steps above in your browser', result.stdout)
                    self.assertNotIn('Installation complete', result.stdout)
                    self.assertNotIn('Opening your browser', result.stdout)
                    self.assertEqual(self.calls(), [])

    @unittest.skipIf(POWERSHELL, 'The claude.ai spelling is a Bash option')
    def test_browser_app_accepts_its_site_name(self):
        result = self.run_installer('claude.ai', {}, ())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('✦ claude.ai\n', result.stdout)
        self.assertIn('claude.ai: finish the steps shown above in your browser', result.stdout)

    @unittest.skipIf(POWERSHELL, 'Several --client values are a Bash option')
    def test_browser_apps_are_summarized_apart_from_the_installed_ones(self):
        result = self.run_installer(None, {}, ('--client', 'codex,chatgpt', '--check'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('Installation complete'), 1, result.stdout)
        self.assertIn('◉ Codex — ✔ installed and connected', result.stdout)
        self.assertIn('◎ ChatGPT — ➜ finish the steps in your browser', result.stdout)
        self.assertIn('Open a new conversation in Codex and type: Show my tasks.', result.stdout)
        self.assertIn('ChatGPT: finish the steps shown above in your browser', result.stdout)
        result = self.run_installer(None, {'connected': False}, ('--client', 'chatgpt,codex', '--check'))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn('Installation complete', result.stdout)
        self.assert_no_mutations()

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The browser is opened by the Bash wizard')
    def test_browser_app_opens_its_page_only_on_request(self):
        page = 'https://chatgpt.com/plugins'
        code, output = self.run_interactive(self.command('chatgpt', ()), [('browser now', 'n')])
        self.assertEqual(code, 0, output)
        self.assertNotIn('Opening your browser', output)
        self.assertEqual(self.calls(), [])
        code, output = self.run_interactive(self.command('chatgpt', ()), [('browser now', 'y')])
        self.assertEqual(code, 0, output)
        self.assertIn('Opening your browser', output)
        # The opener is detached from the wizard, so its record may land after the exit.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and [page] not in [call[1:] for call in self.calls()]:
            time.sleep(0.1)
        self.assertEqual([call[1:] for call in self.calls()], [[page]])

    @unittest.skipIf(POWERSHELL or os.name == 'nt', 'The menu runs in the Bash wizard')
    def test_menu_offers_the_browser_apps_without_any_installed_app(self):
        for client in ('codex', 'claude', 'cursor-agent'):
            (self.bin / client).unlink()
        # Only the doubles and the system tools remain, so no real app is found.
        (self.bin / 'jq').symlink_to(shutil.which('jq'))
        self.env['PATH'] = os.pathsep.join([str(self.bin), os.path.dirname(sys.executable), '/usr/bin', '/bin'])
        prompt = 'Where should Nestor be installed'
        # Enter checks claude.ai, the first row; Down twice and Enter launches from the last line.
        code, output = self.run_interactive(self.command(None, ()),
                                            [(prompt, ''), (prompt, DOWN * 2), ('browser now', 'n')])
        self.assertEqual(code, 0, output)
        self.assertIn('\x1b[38;5;117m☑\x1b[0m \x1b[38;5;209m✦\x1b[0m claude.ai — set up in your browser', output)
        self.assertIn('https://claude.ai/customize/connectors', output)
        self.assertIn('claude.ai: finish the steps shown above in your browser', output)
        self.assertTrue(all(call[0] == 'gum' for call in self.calls()), self.calls())


if __name__ == '__main__':
    unittest.main()
