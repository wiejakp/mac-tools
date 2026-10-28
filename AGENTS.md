# Agent Instructions

This repository holds local personal scripts and shared automation code. Add independent tools as new scripts; keep reusable logic in `src/local_scripts` and behavior tests in `tests`.

## User interaction preferences — mandatory

- Never use Vim, vi, Neovim or Vim-based editors for any task. Use native read/write/edit tools and explicit noninteractive commands.
- Never launch interactive pagers or report viewers, including `less` and `more`. Use `git --no-pager` when Git output might otherwise open a viewer.
- Show final results directly in the main Terminal or editor output. Cleanup results must include disk space before/after and space saved without requiring any further input.
- After an interactive menu run, keep the completed summary visible until the user chooses to close it. A single plain “Press Enter to close this window” action is allowed only after the full before/after/savings result is printed and flushed. Never require a key to reveal the result.
- Explicit `--dry-run` and `--yes` commands must return normally without a closing pause. Quitting the initial menu must also exit immediately.
- Saved reports are background diagnostics, not a required part of the user flow. Keep summaries concise and immediately visible.
- Interactive network mounting also shows its complete result before a single Enter-to-close action. Network `--dry-run` must return without a pause or credential prompts.

## Local scope and privacy

- Determine the repository identity with `git rev-parse --show-toplevel` before using persistent tools. Never use another repository's CCE index.
- Keep source code, filenames, logs, credentials and derived project information local. Do not use hosted analysis, remote memory or external AI APIs.
- Work inside this repository. The existing cleaners are explicitly scoped to `~/sites`; other external paths require an explicit user request.
- Never follow symlinks outside the intended root or access cloud storage, including File Provider directories.
- Never print or index `.env` contents, credentials, private keys or database data. Runtime reports contain action paths and counts only.
- Network mount tools may check reachability, retrieve the home server's SMB share catalogue (share names/types only), and request mounts. The user explicitly prohibits inspecting contents inside work and home shares: never browse or enumerate their files/folders, open their Finder windows or read mounted files. Tests must simulate all server connections, catalogues and mounts.

## Script contracts

- Give each tool one documented purpose, `--help`, deterministic exit codes and a preview mode for destructive work.
- Destructive tools must require an interactive choice or an explicit `--yes` when used noninteractively. Never run cleanup against real apps merely to test implementation.
- `clear-logs.sh` must never remove cache contents. `clear-cache.sh` must never remove application logs.
- Both cleaners use `src/local_scripts/sites_cleaner.py`. Keep path classification in the discovery code and deletion in the descriptor-based execution code.
- Preserve application uploads, databases, sessions, dependencies, Git metadata, source fixtures and archived test/worktree environments.
- Never run application code, elevate privileges, install dependencies or restart services as part of cleanup.
- Keep terminal progress concise; write detailed action reports to ignored `logs/` files. Directory and file-data totals are logical sizes, not a guarantee of immediately freed disk space.
- Disk summaries compare volume capacity and used/free space, with percentages, estimated preview savings and measured cleanup changes. Estimate from allocated blocks of single-link files on the root volume; label projections and measurements separately. Capture usage around cleanup and report unavailable statistics honestly.
- Keep previews readable: group file counts and sizes by directory, sort largest first, and display only a bounded number of the largest directories. Do not print file-by-file lists, discovery lists or repeated notices to Terminal.
- Both preview and cleanup use one updating status line, including when color is disabled. Keep all file paths and sizes in the detailed report; bound noninteractive output and repeated errors.
- Mounting uses `src/local_scripts/network_mounts.py`. `mount.sh` runs work and home independently; `mount-home.sh` selects home; `mount-cch.sh` selects the CCH work SMB profile. Keep mounts sequential and timeout-bound. Skip unreachable home servers before credentials; a failed quick CCH check must not block the native macOS mount attempt. An empty CCH username skips that profile.
- Support an explicitly supplied full CCH hostname/IP through `--cch-server` without changing its share/subfolder or home settings. Do not guess work DNS suffixes or claim a live connection was verified without evidence.
- Detect home drives from authenticated SMB share metadata; never hardcode SSD names, counts or assumed subfolders. Display detected disk shares and offer Mount all (also `--all`) or individual selections. Reuse the home credentials for catalogue lookup and selected mounts, without exposing passwords in arguments or output.
- Work and home credentials must remain separate. Prompt for passwords privately; never store credentials in files, pass passwords in process arguments, print native error payloads or send credentials to a different host. `config/mounts.local.json` stores paths/settings only and stays ignored by Git.

## Development

- Prefer the Python standard library and POSIX shell. The supported Python floor is 3.9 on macOS.
- Use targeted searches. Route large command output through local context-mode when available. CCE is useful only if its server matches this exact repository.
- Write tests for deletion boundaries and failure handling using disposable directories inside `tests/`. Never use live app directories as test fixtures.
- Run `make verify` before claiming completion. Run real-app discovery or previews only when the task authorizes them; do not turn previews into cleanup runs.
- Document every new entry point in README and update its affected tests. Preserve unrelated pre-existing personal scripts.
- Do not add remotes, publish, schedule jobs or send messages without an explicit request.
