# Superpowers plans across clients

Use the installed shared Superpowers skills rather than memorizing an old version.
The shared `superpowers` directory contains the same skill source for each client;
runtime tool availability and model policies still differ.

1. For an unfamiliar failure, use `superpowers:systematic-debugging` to gather
   evidence and isolate a cause before patching it.
2. For new functionality, read `superpowers:brainstorming`, size the design to the
   task, and obtain its required design agreement.
3. Use `superpowers:writing-plans` to write a concrete implementation plan in
   `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`, linked to its design/spec in
   `docs/superpowers/specs/`. Include exact files, interfaces, constraints, test
   cases, and verification commands. Review before implementation when required.
4. Preserve the user's execution choice. For direct/native execution, read
   `superpowers:executing-plans`; for explicitly chosen implementation subagents,
   read `superpowers:subagent-driven-development`. Do not invent delegation support.
5. Track completed steps and decisions in a local ledger so resumed sessions do
   not repeat work. Apply `superpowers:test-driven-development` to behavior changes
   and `superpowers:verification-before-completion` before success claims.

Map a skill's named tool to the equivalent available capability in the current
client. If none exists, state that limitation and use the documented local fallback.
Sharing a skill does not prove its provider-specific hooks are installed.
