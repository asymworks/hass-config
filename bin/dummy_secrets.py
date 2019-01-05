#!/usr/bin/env python3
#

import os, re, sys

# Regexes
re_include = re.compile(r'!include +(.*\.ya?ml) *$')
re_secret = re.compile(r'!secret +(.*) *$')

# Prevent Loops
files = []
secrets = []

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
				scan_file(m.group(1))
			m = re_secret.search(line)
			if m:
				secrets.append(m.group(1))

if __name__ == '__main__':
	if 'TRAVIS_BUILD_DIR' in os.environ:
		os.chdir(os.environ['TRAVIS_BUILD_DIR'])

	scan_file('configuration.yaml')

	with open('secrets.yaml', 'w') as f:
		for s in secrets:
			f.write('{}: dummy\n'.format(s))

	sys.exit(0)