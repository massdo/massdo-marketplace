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
with Path(os.environ['NESTOR_TEST_LOG']).open('a') as log:
    log.write(json.dumps([client, *args]) + '\n')
endpoint = 'https://journal.mcp-marketplace.org/mcp'
skills = ['nestor', 'activity', 'tree', 'pause', 'resume', 'check-for-updates']

def emit(value):
    print(json.dumps(value), flush=True)

if state.get('network_failure'):
    sys.exit(1)
if '--help' in args or args == ['--version']:
    print('test client: --json --scope --stdio')
elif args[:2] == ['plugin', 'list']:
    if state.get('invalid_json'):
        print('invalid json'); sys.exit(0)
    entries = []
    if state.get('installed', True):
        entries = [{'id': 'nestor@massdo-marketplace', 'pluginId': 'nestor@massdo-marketplace',
                    'scope': 'user', 'enabled': state.get('enabled', True)}]
    emit({'installed': entries} if client == 'codex' else entries)
elif args[:3] == ['mcp', 'get', 'nestor']:
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
    print('Component inventory\n  Skills (6)  ' + ', '.join([] if state.get('disabled_skill') else skills))
elif args[:3] == ['mcp', 'get', 'plugin:nestor:nestor']:
    print('  Status: ' + ('✔ Connected' if state.get('connected', True) else '✘ Needs authentication'))
    print('  URL: ' + state.get('url', endpoint))
else:
    print('unsupported test command', file=sys.stderr)
    sys.exit(1)
