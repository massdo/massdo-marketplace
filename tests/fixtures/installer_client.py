#!/usr/bin/env python3
"""Offline client double; its state and call log belong to one test directory."""
import json
import os
import sys
from pathlib import Path

state_path = Path(os.environ['NESTOR_TEST_STATE'])
state = json.loads(state_path.read_text())
client = Path(sys.argv[0]).name
args = sys.argv[1:]
if args[:1] == ['--fixture-client']:
    client, args = args[1], args[2:]
with Path(os.environ['NESTOR_TEST_LOG']).open('a') as log:
    log.write(json.dumps([client, *args]) + '\n')
endpoint = 'https://journal.mcp-marketplace.org/mcp'
skills = ['nestor', 'activity', 'tree', 'pause', 'resume', 'check-for-updates']

def save():
    state_path.write_text(json.dumps(state))


def emit(value):
    print(json.dumps(value), flush=True)


def text(value):
    print('\033[32m' + value + '\033[0m' if state.get('color') else value)


if state.get('network_failure'):
    sys.exit(1)
if '--help' in args or args == ['--version']:
    if state.get('incompatible'):
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
    emit({'installed': entries} if client == 'codex' else entries)
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
            result = {'data': [{'name': 'nestor', 'pluginId': 'nestor@massdo-marketplace',
                'httpOrigin': 'https://journal.mcp-marketplace.org',
                'authStatus': 'oAuth' if state.get('connected', True) else 'notLoggedIn',
                'runtimeStatus': None, 'toolsError': state.get('tools_error'),
                'tools': {} if state.get('missing_tools') else {'get_item': {'name': 'get_item'}}}]}
        else:
            emit({'id': request['id'], 'error': {'message': 'unsupported'}}); continue
        emit({'id': request['id'], 'result': result})
elif args[:2] == ['plugin', 'details']:
    text('Component inventory\n  Skills (6)  ' + ', '.join([] if state.get('disabled_skill') else skills))
elif args[:3] == ['mcp', 'get', 'plugin:nestor:nestor']:
    if not state.get('installed', True) or state.get('missing_server'):
        sys.exit(1)
    text('  Status: ' + ('✔ Connected' if state.get('connected', True) else '✘ Needs authentication'))
    text('  URL: ' + state.get('url', endpoint))
elif args[:2] == ['mcp', 'login']:
    if state.get('refuse_oauth'):
        sys.exit(1)
    state['connected'] = True
    save()
else:
    print('unsupported test command', file=sys.stderr)
    sys.exit(1)
