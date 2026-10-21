# Local Scripts

Personal automation tools with shared code, fixture tests and instructions for AI coding agents. Everything runs locally; no AI service, account, network access or package installation is needed to run the cleaners.

## Available scripts

| Script | Purpose | Report |
| --- | --- | --- |
| `clear-logs.sh` | Remove application runtime logs and rotated `.log` files under `~/sites` | `logs/clear-logs.log` |
| `clear-cache.sh` | Remove known framework and developer tool caches under `~/sites` | `logs/clear-cache.log` |

Each script opens a menu when run in Terminal. Choose **1** to clean, **2** to preview or **Q** to quit. The interface shows timestamps, app discovery, cleanup locations, live file progress and a final summary. The report records every file action and appends each run.

```sh
cd ~/Desktop/scripts
./clear-logs.sh                # Interactive menu
./clear-cache.sh              # Interactive menu
./clear-logs.sh --dry-run      # Preview logs
./clear-cache.sh --dry-run     # Preview caches
./clear-logs.sh --yes          # Clean logs without a menu
./clear-cache.sh --yes         # Clean caches without a menu
```

For double-click use in Finder, open **`launchers/Clear Logs.command`** or **`launchers/Clear Cache.command`**. These are standard macOS Terminal launchers for the matching `.sh` tools. The `.sh` files also carry per-file Terminal Open With metadata on this Mac. The menu flows are covered by pseudo-terminal tests. Keep the entry points together with this project; they share the Python engine in `src/`.

## Cleanup scope

The default root is `~/sites`. Nested applications are recognized from framework entry points and language project manifests. The cleaners do not execute those applications.

- Symfony: `var/cache`, `var/log`, `var/logs`, legacy `app/cache` and `app/logs`.
- Laravel: `storage/logs`, `storage/framework/cache`, compiled views in `storage/framework/views`, and `bootstrap/cache`.
- JavaScript tools: `.next/cache`, `.nuxt/cache`, `.angular/cache`, `.cache`, `.parcel-cache`, `.turbo`, Vite caches and common lint cache files.
- Test/language tools: PHPUnit, pytest, mypy, Ruff and Python `__pycache__` directories.
- Outside excluded locations, log cleanup recognizes `.log` and rotated names such as `.log.1.gz` or `.log-20261021`.

Uploads, databases, sessions, dependencies, Git files, source fixtures, saved test artifacts and temporary worktree copies are preserved. Only `.cache` and `.vite` inside `node_modules` are eligible. Symlinks and cloud-backed paths are skipped. Cache/log root directories and keep files such as `.gitignore` remain in place.

These are allowlisted runtime caches, rather than every directory with “cache” in its name. Global package caches, generated production assets and service memory caches are outside scope. Log mode skips cache trees; cache mode skips log trees. Applications may create new runtime files after cleanup.

Requires macOS and Python 3.9 or newer at `/usr/bin/python3`. Exit status: `0` success or preview complete, `1` cleanup/scan error, `2` invalid arguments or missing explicit noninteractive mode, `130` interrupted.

## Development and agent work

Read [AGENTS.md](AGENTS.md) before changing tools. [Adding scripts](docs/adding-scripts.md) describes how to extend the project.

```sh
make verify
```

Verification checks shell/Python syntax and runs deletion tests in disposable directories inside this repository. It does not clean real applications. Existing personal scripts are preserved and can be incorporated individually.

```text
clear-logs.sh / clear-cache.sh  Public entry points
launchers/                     Double-click macOS Terminal launchers
src/local_scripts/             Reusable implementations
tests/                         Disposable fixture tests
docs/                          Contributor and implementation notes
logs/                          Local reports, ignored by Git
AGENTS.md                      Agent scope, privacy and verification rules
```
