# Agent Instructions

This repository holds local personal scripts and shared automation code. Add independent tools as new scripts; keep reusable logic in `src/local_scripts` and behavior tests in `tests`.

## Local scope and privacy

- Determine the repository identity with `git rev-parse --show-toplevel` before using persistent tools. Never use another repository's CCE index.
- Keep source code, filenames, logs, credentials and derived project information local. Do not use hosted analysis, remote memory or external AI APIs.
- Work inside this repository. The existing cleaners are explicitly scoped to `~/sites`; other external paths require an explicit user request.
- Never follow symlinks outside the intended root or access cloud storage, including File Provider directories.
- Never print or index `.env` contents, credentials, private keys or database data. Runtime reports contain action paths and counts only.

## Script contracts

- Give each tool one documented purpose, `--help`, deterministic exit codes and a preview mode for destructive work.
- Destructive tools must require an interactive choice or an explicit `--yes` when used noninteractively. Never run cleanup against real apps merely to test implementation.
- `clear-logs.sh` must never remove cache contents. `clear-cache.sh` must never remove application logs.
- Both cleaners use `src/local_scripts/sites_cleaner.py`. Keep path classification in the discovery code and deletion in the descriptor-based execution code.
- Preserve application uploads, databases, sessions, dependencies, Git metadata, source fixtures and archived test/worktree environments.
- Never run application code, elevate privileges, install dependencies or restart services as part of cleanup.
- Keep terminal progress concise; write detailed action reports to ignored `logs/` files. A reported byte total is logical file data, not a guarantee of immediately freed disk space.

## Development

- Prefer the Python standard library and POSIX shell. The supported Python floor is 3.9 on macOS.
- Use targeted searches. Route large command output through local context-mode when available. CCE is useful only if its server matches this exact repository.
- Write tests for deletion boundaries and failure handling using disposable directories inside `tests/`. Never use live app directories as test fixtures.
- Run `make verify` before claiming completion. Run real-app discovery or previews only when the task authorizes them; do not turn previews into cleanup runs.
- Document every new entry point in README and update its affected tests. Preserve unrelated pre-existing personal scripts.
- Do not add remotes, publish, schedule jobs or send messages without an explicit request.
