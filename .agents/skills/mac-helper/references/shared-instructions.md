# Shared local agent guidance

Use `~/.agents/skills` as the canonical personal skill library. Read a relevant
`SKILL.md` when its description matches the task. Codex, Claude Code, and Gemini
use the same source through their discovery locations; do not maintain edited
copies per client. Provider-managed system skills remain provider-managed.

For Mac assistance, load `mac-helper/SKILL.md`. Keep facts in a private local
inventory and refresh observations when a decision depends on them. Do not claim
to know everything about the machine.

For repository work, establish the exact Git root first. Use only that root's
local CCE index. Discover available tools in the current client; use local CLI
fallbacks when an MCP capability is missing. A configured server is not proof of
a live connection. Keep MCP transport failures separate from index health.

Use context-mode for large command results and return bounded findings. Use
focused local reads and literal searches for small, known targets. Never index
secrets or pass private project data to hosted analysis, remote memory, remote
embeddings, or an additional AI service. Only the assistant provider explicitly
chosen by the user may receive the task context.

Read installed Superpowers skills for their actual workflows. For substantial
new work: agree a design, write a plan, use the approved execution method, test,
and verify. Native/direct execution means the current agent implements the plan;
it does not imply approval to publish, push, or install unrelated software.

Respect the active task's filesystem scope. Do not traverse the home directory,
follow links outside approved roots, inspect mounted share contents, or access
cloud/File Provider storage. Agent setup may use specifically approved agent
configuration paths. Never print credentials or serial numbers.

Preserve existing instructions, configuration, source, and personal scripts.
Preview destructive actions and require an explicit choice or `--yes`. Back up
important global configuration before writing it. Use noninteractive editing;
never launch Vim, vi, Neovim, less, or more. Print concise results directly.
