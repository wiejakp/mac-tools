# Agent guide

## Purpose

This repository maintains the user's local macOS tools. It separates application
log cleanup from cache cleanup, mounts explicitly selected SMB locations, and
supports local coding-agent setup. The agent's job is to understand and maintain
those tools within the user's request, preserving user data and existing work.

Safety and privacy come first. Keep private information local except for the
active assistant service the user selected. Additional services require explicit
permission for the destination and data. A network-enabled command or available
plugin is not permission to transfer project information.

## Entry points and source map

| Area | Entry points | Implementation |
| --- | --- | --- |
| Codex | `make codex` | Direct native recipe in `Makefile` |
| Cursor Agent | `make agent` | Direct native recipe; `.cursor/` settings and rule |
| Gemini CLI | `make gemini` | Direct native recipe; `.gemini/settings.json`, `GEMINI.md` |
| Log/cache cleanup | `clear-logs.sh`, `clear-cache.sh` | `src/local_scripts/sites_cleaner.py` |
| SMB mounting | `mount.sh`, `mount-home.sh`, `mount-cch.sh` | `src/local_scripts/network_mounts.py` |
| Agent setup | `agent-setup.sh --help` | `src/local_scripts/agent_setup.py` |
| Behavior checks | `make verify` | Disposable fixtures in `tests/` |
| Operating rules | `AGENTS.md` | Purpose, boundaries, workflow and contracts |
| Task audit | `docs/change-records/` | Exact actions, results and rollback steps |
| Local recovery | Ignored `logs/change-backups/` | Prior bytes, modes and absent paths |

Use `make help` for existing shortcuts. The direct Codex recipe is retained;
initialization adds no wrapper, daemon or package installation.

## Skills

The Mac helper's actual files are stored in `.agents/skills/mac-helper/`, where
native local skill discovery can read them directly. This is a physical
directory inside the project, with no discovery symlink. The existing
personal skill library remains `~/.agents/skills`, with provider-managed system
skills kept under their provider. This guide grants no permission to enumerate
external library paths or change global agent settings.

Select skills from the catalog actually available in the current client:

| Need | Existing skill |
| --- | --- |
| Mac assistance, local agent setup and tool diagnostics | `mac-helper` |
| Understand a fault before fixing it | `superpowers:systematic-debugging` |
| Develop substantial new behavior and its plan | Installed Superpowers brainstorming/planning workflow |
| Add behavior with meaningful regression coverage | `superpowers:test-driven-development` |
| Check evidence before claiming success | `superpowers:verification-before-completion` |
| Process large local results | `context-mode:context-mode`, when already accessible |
| Create or revise an actual skill | Available skill-creation/writing skill |

Project-local `cce-maintenance`, `agent-orchestration` and `skill-validation`
skills are copied and adapted from `app_hublist`. Every coding client must use
local CCE for semantic retrieval and local CTX for large outputs/session context.
[Client setup](agent-clients.md) documents installation, native configuration,
health checks and the global Codex hook repair.

Read the selected skill's instructions rather than relying on its name. Prefer
the smallest relevant set. Skills and plugins do not extend task scope, approve
network transfers or bypass filesystem restrictions. Use a single agent by
default; delegate only when the user or applicable instructions explicitly call
for it. Installing or changing shared skills is a separate scoped change.

## Coding workflow

1. Confirm the Git root and read `AGENTS.md`. Check the working tree and preserve
   pre-existing changes. State the task's outcome and boundaries.
2. Retrieve only relevant context. Use the matching local CCE index when already
   accessible, literal `rg` for known identifiers, and structural tools for syntax
   questions. Process large results locally. Use bounded CLI fallback rather
   than requesting CCE/context-mode access approval.
3. Before any implementation mutation, create a change record and capture exact
   prior bytes and modes, including untracked files and absent paths. Name every
   affected setting, process and file. Write executable rollback instructions
   that check for later changes before overwriting anything.
4. Reuse native commands and established project patterns. Add executable code,
   dependencies or global changes only when necessary for the requested outcome.
   Prefer Python's standard library, Python 3.9 compatibility and POSIX shell.
5. For behavior changes, reproduce the issue and run the smallest meaningful
   check first. Use disposable repository fixtures for deletion boundaries and
   simulated mounts. Review the diff and run `make verify` before completion.
6. Record the actual results and limitations. Verify recovery in disposable
   fixtures when changing the recovery procedure. Remove only owned temporary
   files/processes. Keep the completed summary visible in Terminal/editor output.

## macOS boundaries

Work inside this exact repository. Additional paths need explicit task scope.
Never access cloud/File Provider storage, secrets, credentials or mounted share
contents. Never follow an escaping symlink. Never use Vim or an interactive pager.
Do not grant new permissions, install packages, restart services or modify global
configuration merely to make initialization or a diagnostic pass.

Cleanup discovery/previews are run only when requested; real cleanup requires
the existing interactive choice or explicit `--yes`. Keep uploads, databases,
sessions, dependencies, source fixtures and Git metadata intact. Mount tests
simulate connections and catalogues and never inspect share contents.

For Mac facts, follow the Mac helper's `references/mac-assistance.md`; refresh
only facts needed for the task. For local skills/CCE/context-mode configuration,
follow `references/agent-tools.md`. Keep package installation, hook approval,
MCP transport and persistent index health as separate observations. Do not claim
any was verified merely because a skill or command exists.

## Recovery and handoff

Each task record must identify its local backups, exact rollback commands,
expected restored behavior and verification results. Restore original file modes
as well as bytes. Refuse rollback when later edits, unexpected directory entries
or unsafe symlinks would be overwritten. Never use a broad Git reset or clean to
undo a scoped task. Preserve unrelated work and retain the local recovery archive.

Initialization's [change record](change-records/2026-10-28-agent-initialization.md)
contains its complete rollback procedure. It affects local documentation and
skill discovery; no global installation is required to undo it.
