# Mac helper and shared local agent setup

## Outcome

This repository supplies local Mac assistance and repeatable agent setup. A single
personal skill library at `~/.agents/skills` serves Codex, Claude Code, and Gemini
CLI. Agent-specific discovery links and instruction files point to that library;
provider tool configuration stays separate.

## Design

- Preserve existing skills and instructions. Move personal Codex skills into the
  shared library only when no conflicting shared entry exists; retain compatibility
  links. Leave Codex's managed `.system` skills in place. Link the other clients'
  skill directories to the same library when those directories are absent.
- Add one portable `mac-helper` skill in this repository and link it into the
  shared library. It routes Mac diagnostics, local CCE/context-mode use, and
  Superpowers planning without assuming a particular provider's tool names.
- Preserve the existing Superpowers installation. Make its shared discovery
  consistent across agents and explain the plan/spec/execution workflow.
- Repair the installed context-mode package by replacing internal npm `.bin`
  symlinks with executable shell forwarders to the original targets. Preserve
  original link metadata in a local backup. Refuse escaping, broken, or unexpected
  links. Do not disable hooks or remove dependencies.
- Initialize CCE for this exact repository using local stdio MCP. Keep index
  health separate from MCP transport health. Prevent model/package downloads
  during verification and use local retrieval only.
- Keep machine observations in an ignored local JSON report: macOS version,
  architecture, hardware model, memory, installed agent executable availability,
  and exact repository identity. Omit serial numbers, account data, network
  identifiers, credentials, and unrelated filesystem inventories.

## Interface and safety

`agent-setup.sh` previews changes by default; `--yes` applies selected repairs or
shared-skill installation. `--help` documents deterministic exits. All important
configuration changes have local backups. Tests use disposable directories under
`tests/` and never touch the real agent configuration or live app directories.
Use Python 3.9+ standard library and POSIX shell. Cloud storage remains excluded.
External agent configuration paths were explicitly approved for this task.

## Verification

Prove the plugin-entry failure with a fixture, test repaired command forwarding,
rejected escaping links, preview immutability, collision preservation, and repeated
installation. Run `make verify`. Exercise the real context-mode hooks without
allowing dependency installs. Verify a real local CCE search and stdio MCP startup.
Report any session restart or unavailable client separately from completed work.
