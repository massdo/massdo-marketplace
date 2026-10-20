#!/usr/bin/env python3
"""Offline client double; its state and call log belong to one test directory."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

state_path = Path(os.environ['NESTOR_TEST_STATE'])
state = json.loads(state_path.read_text())
client = Path(sys.argv[0]).name
args = sys.argv[1:]
if args[:1] == ['--fixture-client']:
    client, args = args[1], args[2:]
with Path(os.environ['NESTOR_TEST_LOG']).open('a') as log:
    log.write(json.dumps([client, *args]) + '\n')
plugin_dir = Path(os.environ['NESTOR_TEST_FIXTURE']).resolve().parents[2] / 'plugins/nestor'
endpoint = json.loads((plugin_dir / 'mcp.json').read_text(encoding='utf-8'))['mcpServers']['nestor']['url']
url = urlsplit(endpoint)
origin = url.scheme + '://' + url.netloc
skills = sorted(path.parent.name for path in (plugin_dir / 'skills').glob('*/SKILL.md'))

def save():
    state_path.write_text(json.dumps(state))


def emit(value):
    print(json.dumps(value), flush=True)


def text(value):
    print('\033[32m' + value + '\033[0m' if state.get('color') else value)


if args == state.get('fail_command'):
    print(state['native_error'], file=sys.stderr)
    if args == ['app-server', '--stdio']:
        request = json.loads(sys.stdin.readline())
        emit({'id': request['id'], 'error': {'message': 'native startup failed'}})
    sys.exit(1)
if state.get('network_failure'):
    sys.exit(1)
if '--help' in args or args == ['--version']:
    if state.get('incompatible') or state.get('missing_capability') == ' '.join(args[:-1]):
        sys.exit(1)
    print('test client: --json --scope --stdio')
elif args[:3] == ['plugin', 'marketplace', 'list']:
    entries = []
    if state.get('marketplace', True):
        entries = [{'name': 'massdo-marketplace', 'source': 'github',
                    'repo': state.get('marketplace_repo', 'massdo/massdo-marketplace'),
                    'marketplaceSource': {'sourceType': 'git', 'source':
                        'https://github.com/' + state.get('marketplace_repo', 'massdo/massdo-marketplace') + '.git'}}]
    emit({'marketplaces': entries} if client == 'codex' else entries)
elif args[:3] == ['plugin', 'marketplace', 'add']:
    state['marketplace'] = True
    save()
elif args[:2] in (['plugin', 'remove'], ['plugin', 'uninstall']):
    state['installed'] = False
    save()
    emit({'removed': True})
elif args[:2] in (['plugin', 'add'], ['plugin', 'install'], ['plugin', 'enable']):
    if state.get('install_failure'):
        sys.exit(1)
    state.update(installed=True, enabled=True)
    if state.get('auto_auth'):
        state['connected'] = True
    save()
    if state.get('partial_install_failure'):
        sys.exit(1)
    emit({'authPolicy': 'ON_INSTALL'})
elif args[:2] == ['plugin', 'list']:
    if state.get('invalid_json'):
        print('invalid json'); sys.exit(0)
    entries = []
    if state.get('installed', True):
        identifier = 'nestor@' + state.get('plugin_marketplace', 'massdo-marketplace')
        entries = [{'id': identifier, 'pluginId': identifier,
                    'scope': state.get('scope', 'user'), 'enabled': state.get('enabled', True)}]
    entries.append({'id': 'other@other', 'pluginId': 'other@other', 'scope': 'user', 'enabled': True})
    if client == 'claude' and state.get('synced'):
        entries.append({'id': 'nestor@synced', 'scope': 'synced', 'enabled': True})
    emit({'installed': entries, 'available': [{'pluginId': 'nestor@massdo-marketplace'}]}
         if client == 'codex' else entries)
elif args[:2] == ['mcp', 'list']:
    emit([{'name': 'nestor', 'transport': {'url': state.get('url', endpoint)}}]
         if state.get('installed', True) or state.get('manual_server') else [])
elif args[:3] == ['mcp', 'get', 'nestor']:
    if client == 'claude':
        sys.exit(0 if state.get('manual_server') else 1)
    if state.get('missing_server'):
        sys.exit(1)
    emit({'enabled': True, 'transport': {'url': state.get('url', endpoint)}})
elif args[:2] == ['app-server', '--stdio']:
    for line in sys.stdin:
        with Path(os.environ['NESTOR_TEST_LOG']).open('a') as log:
            log.write(json.dumps([client, 'rpc-input', line]) + '\n')
        request = json.loads(line)
        method = request['method']
        if 'id' not in request:
            continue
        if method == 'initialize':
            result = {}
        elif method == 'skills/list':
            result = {'data': [{'skills': [
                {'name': 'nestor:' + skill, 'enabled': not state.get('disabled_skill')}
                for skill in skills]}]}
        elif method == 'mcpServerStatus/list':
            tools = {} if state.get('missing_tools') else {'get_item': {'name': 'get_item'}}
            if state.get('tools_array'):
                tools = list(tools.values())
            result = {'data': [{'name': 'nestor', 'pluginId': 'nestor@massdo-marketplace',
                'httpOrigin': origin,
                'authStatus': state.get('auth_status', 'oAuth' if state.get('connected', True) else 'notLoggedIn'),
                'runtimeStatus': state.get('runtime_status'), 'toolsError': state.get('tools_error'),
                'tools': tools}]}
        else:
            emit({'id': request['id'], 'error': {'message': 'unsupported'}}); continue
        emit({'id': request['id'], 'result': result})
elif args[:2] == ['plugin', 'details']:
    text('Component inventory\n  Skills (' + str(len(skills)) + ')  ' + ', '.join([] if state.get('disabled_skill') else skills))
elif args[:3] == ['mcp', 'get', 'plugin:nestor:nestor']:
    if not state.get('installed', True) or state.get('missing_server'):
        sys.exit(1)
    status = '✔ Connected' if state.get('connected', True) else '✘ Needs authentication'
    if state.get('offline'):
        status = '✘ Failed to connect'
    if state.get('tools_error'):
        status = '! Connected · tools fetch failed'
    text('  Status: ' + status)
    text('  URL: ' + state.get('url', endpoint))
elif args[:2] == ['mcp', 'login']:
    expected = 'plugin:nestor:nestor' if client == 'claude' else 'nestor'
    if args[2:] != [expected]:
        print('wrong MCP server', file=sys.stderr)
        sys.exit(1)
    if state.get('refuse_oauth'):
        sys.exit(1)
    state['connected'] = True
    save()
elif args[:2] == ['mcp', 'logout']:
    expected = 'plugin:nestor:nestor' if client == 'claude' else 'nestor'
    if args[2:] != [expected]:
        print('wrong MCP server', file=sys.stderr)
        sys.exit(1)
    state['connected'] = False
    save()
elif client == 'cursor-agent' and args[:3] == ['mcp', 'list-tools', 'nestor']:
    if state.get('offline'):
        print('Failed to connect', file=sys.stderr)
        sys.exit(1)
    if not state.get('connected', True):
        print('Needs authentication', file=sys.stderr)
        sys.exit(1)
    if not state.get('missing_tools'):
        text('get_item — Read a Nestor item')
else:
    print('unsupported test command', file=sys.stderr)
    sys.exit(1)
