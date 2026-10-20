#!/usr/bin/env python3
"""Offline double for the gum menu tool: prompts on stderr, one line read from the terminal."""
import json
import os
import sys

args = sys.argv[1:]
log = os.environ.get('NESTOR_TEST_LOG')
if log:
    with open(log, 'a') as handle:
        handle.write(json.dumps(['gum', *args]) + '\n')
command = args[0] if args else ''
if '--help' in args:
    print('Usage: gum ' + command + ' [flags]\n      --label-delimiter=""   label:value options\n      --selected=,...')
    sys.exit(0)
flags = {}
positional = []
for argument in args[1:]:
    if argument.startswith('--'):
        name, _, value = argument.partition('=')
        flags[name] = value
    else:
        positional.append(argument)
if command == 'choose':
    delimiter = flags.get('--label-delimiter', '')
    sys.stderr.write(flags.get('--header', 'Choose:') + '\n')
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        sys.exit(130)
    wanted = [item.strip() for item in line.strip().split(',') if item.strip()]
    chosen = []
    for option in positional:
        label, value = (option.split(delimiter, 1) if delimiter and delimiter in option else (option, option))
        if label in wanted or value in wanted:
            chosen.append(value)
    if chosen:
        print('\n'.join(chosen))
elif command == 'confirm':
    sys.stderr.write((positional[0] if positional else 'Confirm?') + ' (y/N) ')
    sys.stderr.flush()
    line = sys.stdin.readline()
    sys.exit(0 if line.strip().lower() in ('y', 'yes') else 1)
elif command == 'spin':
    import subprocess
    sys.exit(subprocess.run(args[args.index('--') + 1:], stdin=subprocess.DEVNULL).returncode if '--' in args else 1)
elif command in ('style', 'format', 'log'):
    print(' '.join(positional))
elif command == '--version':
    print('gum version v2.0.2')
else:
    print('unsupported gum command', file=sys.stderr)
    sys.exit(1)
