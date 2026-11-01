# Agent Instructions

This repository holds local personal scripts and shared automation code. Add independent tools as new scripts; keep reusable logic in `src/local_scripts` and behavior tests in `tests`.

## Purpose and agent startup

Maintain the user's local macOS tools: separate site log/cache cleaners, SMB
mounting helpers and local agent setup. Favor the existing native commands and
small, verifiable changes. This role does not grant general access to the Mac.

At the start of a task:

1. Confirm the exact Git root and read these instructions. Preserve existing
   uncommitted work.
2. Read [the agent guide](docs/agent-guide.md) for the purpose, code map and
   workflow. For Mac or agent-setup tasks, apply the existing
   [Mac helper skill](.agents/skills/mac-helper/SKILL.md), stored directly in
   this project's `.agents/skills/mac-helper` directory.
3. Select relevant skills from the current skill catalog. Use systematic
   debugging for faults, the installed planning workflow for substantial new
   behavior, and verification before claiming completion. Read each applicable
   skill's instructions; skill availability does not grant filesystem access.
4. Before implementation, write the task's change record and preserve original
   bytes, permissions and absent paths. Include exact rollback steps.
5. Execute the smallest authorized change, verify it and update the record with
   results, limitations and recovery information. Use one agent unless the user
   or an applicable skill explicitly requests delegation.

## Safety, privacy and reversible changes — mandatory

- Safety and privacy take priority over convenience. Keep private source, filenames, metadata, logs, credentials and derived information local. Any transfer to another service requires the user's explicit permission for that destination and data; this session's assistant authorization does not authorize additional services.
- Before the first mutation for every task, create a local change record in `docs/change-records/` describing the requested outcome, exact files/settings/processes affected, ordered actions, risks, verification commands and numbered rollback steps. Update it as the work changes and record the final results and limitations.
- Save the existing contents and permissions of every affected file before changing or deleting it, including untracked files. Record paths that did not exist. Keep recovery data inside ignored `logs/change-backups/`; never include credentials or secret files. Preserve unrelated changes.
- Do not start a change without a concrete rollback procedure for every planned effect. Rollback must name exact paths and commands, restore the captured state and check for later user edits before overwriting anything. An unavoidable irreversible action needs explicit user authorization before execution.
- Prefer existing native commands and verified project patterns. Add scripts, dependencies, background processes or global configuration changes only when necessary for the requested outcome. Document their purpose and removal steps first.
- Verify the changed behavior and report failed checks honestly. Stop and clean up owned diagnostic processes and disposable fixtures; never terminate unrelated sessions or alter unrelated functionality to make a check pass.
- Never request CCE or context-mode access approvals. Use bounded direct local commands when those tools need approval; this preference takes precedence over the retrieval instructions below.

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

## Coding clients and required local tools

- `make codex`, `make agent` (Cursor) and `make gemini` start the existing native
  CLIs in this project. See [installation and usage](docs/agent-clients.md).
- All clients must use this exact repository's local CCE for semantic retrieval
  and local context-mode (CTX) for large tool output and applicable session memory.
  Verify the Git root and server identity first; never borrow another index.
- Cursor reads `.cursor/mcp.json`, `.cursor/hooks.json` and its always-applied
  rule. Gemini reads `.gemini/settings.json` and `GEMINI.md`. Their MCP servers
  use local stdio processes and explicitly pin this repository as their cwd.
- Local instructions and skills do not authorize another assistant provider,
  hosted MCP, cloud worker, remote embeddings or credentials. Starting another
  provider's session requires the user's choice. No client is launched to test
  it by sending private repository content to a model.
- If a required transport or hook is unavailable, report the actual failure and
  use bounded local CLI fallback. Keep hook trust, package integrity, MCP
  reachability and persistent index health as separate observations.

## Context Engine (CCE)

This project uses Code Context Engine for intelligent code retrieval and
cross-session memory.

### Searching the codebase

**Use `context_search` instead of reading files directly** when exploring
the codebase, answering questions about code, or understanding how things
work. `context_search` returns the most relevant code chunks with
confidence scores instead of whole files.

When to use `context_search`:
- Answering questions about the codebase ("how does X work?", "where is Y?")
- Exploring structure or architecture
- Finding related code, functions, or patterns

Other tools:
- `expand_chunk` for full source of a compressed result
- `related_context` for what calls/imports a function
- `session_recall` to recall past decisions

### Cross-session memory

Call `session_recall("topic phrase")` before answering non-trivial questions.
Call `record_decision(decision="...", reason="...")` after making choices.
Call `record_code_area(file_path="...", description="...")` after meaningful work.
