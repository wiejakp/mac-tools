# Context, Translation, and Handoffs

## Local context

Confirm `git rev-parse --show-toplevel` before persistent retrieval. CCE must be a
local stdio server bound to that exact root. Use `context_search` to locate
implementation, `related_context` for relationships and `expand_chunk` only when
exact source is needed. Never query another project's index.

Use local context-mode for large output and prior decisions that affect the task.
Process raw data in `ctx_execute`, `ctx_execute_file` or `ctx_batch_execute` and
return bounded findings. Batch related searches. Never index secrets or bypass a
denied filesystem path. If a transport is unavailable, report it separately from
persistent index health and use the documented local CLI fallback.

## Authorized context packet

Include only the task outcome, applicable constraints, exact read/write scope,
dependencies, relevant local snippets or paths, expected result and focused
verification command. Do not copy the complete parent conversation by default.
The packet does not grant access beyond the user's authorization.

A worker's handoff includes changed paths, result, command/exit evidence,
limitations and unresolved decisions. The main agent reviews changes before
integration and owns the combined result.

## Translation work, when requested

Freeze source text before any authorized translation work. Keep locale files
disjoint and preserve placeholders, links, code and structural identifiers.
Review translated content and terminology before integration. Translation does
not create an exception to the explicit delegation requirement.
