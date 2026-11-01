@./AGENTS.md

# Gemini project entry point

Read [the agent guide](docs/agent-guide.md) and
[client setup](docs/agent-clients.md). Skills are physical project files under
`.agents/skills/`; load the relevant `SKILL.md` before applying a skill.

You must use the matching local CCE server for semantic repository retrieval and
local context-mode (CTX) for large outputs and applicable session context. Check
the exact Git root before persistent retrieval, verify the connected server and
never use another project's index. Process large data locally and report bounded
results. Report unavailable transports honestly and use the local CLI fallback.

This Gemini session is authorized only when the user chooses Gemini for the task.
It does not authorize sending data to additional services, cloud workers or remote
MCP servers. Never read/index credentials or cloud storage. Follow the mandatory
change-record, backup and rollback rules in AGENTS.md. Use disposable test
fixtures and simulated network mounts; run `make verify` before completion.
