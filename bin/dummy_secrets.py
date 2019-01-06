#!/usr/bin/env python3
#

import os, re, sys

# Regexes
re_include = re.compile(r'!include\s+(?P<filename>.*\.ya?ml)\s*$')
re_secret = re.compile(r'!secret\s+(?P<key>\w+?)(\s*# dummy:?\s+(?P<default>.*))?\s*$')

# Prevent Loops
files = []
secrets = {}

def scan_file(filename):
	abs_fn = os.path.abspath(filename)
	if abs_fn in files:
		raise RuntimeError('Include Loop Detected for %s' % (abs_fn))
	if not os.path.isfile(filename):
		raise RuntimeError('Could not open %s' % (abs_fn))
	with open(abs_fn, 'r') as f:
		files.append(abs_fn)
		for line in f:
			m = re_include.search(line)
			if m:
				scan_file(m.group('filename'))
			m = re_secret.search(line)
			if m:
				key = m.group('key')
				if key not in secrets.keys():
					secrets[key] = 'dummy'
					if 'default' in m.groupdict().keys():
						secrets[key] = m.group('default')

if __name__ == '__main__':
	if 'TRAVIS_BUILD_DIR' in os.environ:
		os.chdir(os.environ['TRAVIS_BUILD_DIR'])

	scan_file('configuration.yaml')
	scan_file('known_devices.yaml')

	with open('secrets.yaml', 'w') as f:
		for k, v in secrets.items():
			f.write('{}: {}\n'.format(k, v))

	sys.exit(0)
