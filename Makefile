PYTHON ?= /usr/bin/python3

.PHONY: help test check verify preview-logs preview-cache

help:
	@printf '%s\n' 'make verify        Shell syntax, Python syntax and fixture tests' 'make preview-logs  Preview app log cleanup' 'make preview-cache Preview app cache cleanup'

test:
	$(PYTHON) -B -m unittest discover -s tests -v

check:
	/bin/sh -n clear-logs.sh
	/bin/sh -n clear-cache.sh
	/bin/sh -n 'launchers/Clear Logs.command'
	/bin/sh -n 'launchers/Clear Cache.command'
	$(PYTHON) -B -c "import ast; from pathlib import Path; files = list(Path('src').rglob('*.py')) + list(Path('tests').glob('*.py')); [ast.parse(p.read_text(), filename=str(p)) for p in files]; print('Python syntax: OK')"

verify: check test

preview-logs:
	./clear-logs.sh --dry-run

preview-cache:
	./clear-cache.sh --dry-run
