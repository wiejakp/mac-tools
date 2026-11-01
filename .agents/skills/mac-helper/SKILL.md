---
name: mac-helper
description: Use when assisting with this Mac, local macOS automation, shared Codex/Claude/Gemini skills, CCE or context-mode setup, or plugin hook failures such as unsupported plugin entry type.
---

# Mac helper

Use verified local observations, one personal skill library, and reversible changes.
This skill works across assistants; tool names and permissions depend on the client.

Start with the active task and its approved filesystem scope. For repository work,
run `git rev-parse --show-toplevel` before persistent retrieval. Read the repository's
`AGENTS.md` and preserve existing personal scripts. This project is
`/Users/pwiejak/Desktop/tools`; resolve its current location rather than assuming a
shell started there.

| Task | Reference |
| --- | --- |
| Mac facts, maintenance, filesystem boundaries | [Mac assistance](references/mac-assistance.md) |
| Shared skill installation, CCE, context-mode, hook recovery | [Agent tools](references/agent-tools.md) |
| A multi-step change or a Superpowers plan | [Planning](references/planning.md) |

Use `<repository>/agent-setup.sh --help` for available setup operations. Previews
are the default; `--yes` applies backed-up changes. `--inventory` prints a small
machine snapshot; `--inventory --yes` also saves ignored local observations.
An observation file records what was checked, not everything installed on the Mac.

Keep project data local except for the active assistant service selected by the
user. Never browse cloud storage, read credentials, or inspect network-share
contents. A skill supplies guidance, not additional filesystem authorization.

Before claiming success, run the relevant command and inspect its exit and result.
Changes in this repository require `make verify`. State separately whether a
package, its hook approval, its MCP transport, and its persistent index were verified.
