PYTHON ?= /usr/bin/python3
CODEX ?= codex
AGENT ?= agent
GEMINI ?= gemini

.PHONY: help codex agent gemini clear cache logs clear-cache clear-logs mount mount-home mount-cch test check verify preview-logs preview-cache preview-mounts

help:
	@printf '%s\n' 'make codex          Codex chat list with automatic approval review' 'make agent          Cursor Agent in this project' 'make gemini         Gemini CLI in this project' 'make clear cache    Interactive cache cleanup (also clear-cache)' 'make clear logs     Interactive log cleanup (also clear-logs)' 'make preview-cache  Preview cache cleanup' 'make preview-logs   Preview log cleanup' 'make mount          Interactive work and home mounting' 'make mount-home     Interactive home mounting' 'make mount-cch      Interactive CCH mounting' 'make preview-mounts Preview configured mounts without connecting' 'make verify         Syntax and disposable fixture tests'

codex:
	@"$(CODEX)" --cd "$(CURDIR)" --strict-config \
		--sandbox workspace-write --ask-for-approval on-request \
		--config 'approvals_reviewer="auto_review"' \
		--config sandbox_workspace_write.network_access=true \
		--enable guardian_approval --enable hooks --enable plugin_hooks agents

agent:
	@"$(AGENT)"

gemini:
	@"$(GEMINI)"

clear:
ifeq ($(filter cache logs,$(MAKECMDGOALS)),)
	@printf '%s\n' 'Choose: make clear cache | make clear logs'
else
	@:
endif

cache clear-cache:
	./clear-cache.sh

logs clear-logs:
	./clear-logs.sh

mount:
	./mount.sh

mount-home:
	./mount-home.sh

mount-cch:
	./mount-cch.sh

test:
	$(PYTHON) -B -m unittest discover -s tests -v

check:
	/bin/sh -n agent-setup.sh
	/bin/sh -n clear-logs.sh
	/bin/sh -n clear-cache.sh
	/bin/sh -n 'launchers/Clear Logs.command'
	/bin/sh -n 'launchers/Clear Cache.command'
	/bin/sh -n mount.sh
	/bin/sh -n mount-home.sh
	/bin/sh -n mount-cch.sh
	/bin/sh -n 'launchers/Mount All.command'
	/bin/sh -n 'launchers/Mount Home.command'
	/bin/sh -n 'launchers/Mount CCH.command'
	$(PYTHON) -B -c "import ast; from pathlib import Path; files = list(Path('src').rglob('*.py')) + list(Path('tests').glob('*.py')); [ast.parse(p.read_text(), filename=str(p)) for p in files]; print('Python syntax: OK')"

verify: check test

preview-logs:
	./clear-logs.sh --dry-run

preview-cache:
	./clear-cache.sh --dry-run

preview-mounts:
	./mount.sh --dry-run
