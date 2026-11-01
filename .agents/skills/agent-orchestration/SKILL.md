---
name: agent-orchestration
description: "Use when deciding whether independent agent work is useful, preparing local CTX/CCE context, or coordinating verification."
---

# Agent Orchestration

Adapted from the app_hublist skill for this repository's Python/Make workflow.

Work inline by default. Current explicit user authorization is required before
delegating a bounded subtask; availability, complexity or a copied workflow does
not grant it. No standing translation or final-suite delegation exceptions apply.

The main agent owns scope, shared files, privacy decisions, integration, final
verification and the task's change record. If delegation is authorized, give each
worker independent file/state ownership and a bounded handoff. Workers must not
expand scope or spawn more workers. Use the actual available model controls;
never require or claim a model that the current client does not offer.

Use this exact repository's local CCE for semantic retrieval and local CTX for
large results and relevant session context. Never send private data to another
provider, hosted MCP service or cloud worker without explicit authorization.
Run the project's focused checks during implementation and `make verify` at the
final gate. Tests use disposable repository fixtures and simulated mounts.

## Reference Routing

- [Decision Gate and Worker Roles](references/decision-gate-and-roles.md): authorization and ownership.
- [Context, Translation, and Handoffs](references/context-translation-and-handoffs.md): local context packets and bounded handoffs.
- [Testing, Planning, and Completion](references/testing-planning-and-completion.md): test ownership, records and completion.
- [Evaluation cases](references/evaluation-cases.json): expected decisions and failure cases.

Before completion, apply [Final Verification](../skill-validation/references/final-verification.md).
