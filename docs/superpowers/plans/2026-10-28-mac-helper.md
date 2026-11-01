# Mac Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair context-mode hook packaging and provide one shared, local Mac-helper skill setup.

**Architecture:** Keep repeatable setup logic in a Python standard-library module and expose a POSIX shell entry point. Store portable skills in the repository, install discovery links in approved agent directories, and retain provider-specific MCP configuration separately.

**Tech Stack:** Python 3.9+, POSIX shell, local CCE CLI, local context-mode MCP.

**Spec:** `docs/superpowers/specs/2026-10-28-mac-helper.md`

## Global Constraints

- Use Python 3.9+ standard library and POSIX shell.
- Cloud storage remains excluded.
- External agent configuration paths were explicitly approved for this task.
- Tests use disposable directories under `tests/` and never touch the real agent configuration or live app directories.
- Preserve existing skills and instructions.

## Review Focus

- Escaping or dangling plugin symlinks must fail before mutation.
- Existing shared skills with different content must be preserved and reported.
- Repeated installs must leave a single source and stable compatibility links.
- Hook checks must not install dependencies or contact remote services.
- A healthy persistent index does not prove the current session has its MCP tools.

### Task 1: Repeatable plugin packaging repair

**Files:** Create `src/local_scripts/agent_setup.py`, `agent-setup.sh`, and `tests/test_agent_setup.py`; update `Makefile` and `README.md`.

**Interfaces:** `repair_plugin(plugin: Path, backup: Path, apply: bool) -> list[str]`; CLI `--repair-context-mode PATH`, default preview, `--yes` apply.

- [ ] Write failing tests for internal executable links, argument forwarding, dry-run immutability, escaping links, broken links, unexpected entries, and idempotence.
- [ ] Run `/usr/bin/python3 -B -m unittest discover -s tests -p test_agent_setup.py -v`; confirm the missing repair behavior fails.
- [ ] Implement bounded traversal, preflight validation, backed-up link metadata, and atomic shell forwarders.
- [ ] Run the targeted tests; preview and apply the repair to the approved context-mode installation.
- [ ] Verify every hook entry and local MCP startup without enabling downloads.

### Task 2: Shared skill discovery and portable Mac guidance

**Files:** Extend `src/local_scripts/agent_setup.py` and `tests/test_agent_setup.py`; add `skills/mac-helper/SKILL.md` and focused references.

**Interfaces:** `install_shared_skills(agent_home: Path, repository: Path, apply: bool) -> list[str]`; CLI `--share-skills`, `--inventory`.

- [ ] Exercise baseline discovery and planning scenarios before authoring guidance; retain concrete missing information.
- [ ] Test collision refusal, preservation of `.system`, previews, missing client directories, and repeat installation with fixture homes.
- [ ] Implement one canonical library, compatibility links, backed-up instruction references, and a sanitized local machine report.
- [ ] Author the portable skill and test discovery/reference scenarios with it.
- [ ] Preview and install the shared layout in approved directories after design approval.

### Task 3: Repository CCE and final verification

**Files:** CCE-generated local configuration, `.gitignore`, `README.md`, and plan checkboxes.

- [ ] Back up affected agent configuration before CCE initialization.
- [ ] Initialize CCE for the exact Git root with local/offline configuration; do not reuse unrelated MCP servers.
- [ ] Verify index status, a harmless project search, and stdio MCP tool availability.
- [ ] Run `make verify`, review the complete changed-file list, refresh only affected CCE paths, and record remaining client/session limitations.
