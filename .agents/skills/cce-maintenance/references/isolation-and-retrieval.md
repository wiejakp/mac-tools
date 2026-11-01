# CCE Repository Isolation and Retrieval

## Repository Isolation

This skill is repository-local.

Never record, reference, enumerate, inspect, infer, or expose:

- sibling repositories;
- unrelated repository names;
- personal project names;
- work projects unrelated to the current repository;
- absolute paths outside the current repository;
- CCE registrations belonging to other repositories;
- local directory structures outside the current repository;
- other repositories listed in global Codex configuration.

Resolve the current repository dynamically when shell-level repository identity is required:

```sh
git rev-parse --show-toplevel
```

All CCE operations governed by this skill must remain scoped to that resolved repository root.

Never hardcode a repository path into this skill.

Never include examples containing actual local repository names or actual local filesystem paths.

Do not inspect:

```text
~/.codex/config.toml
```

to discover other repositories unless the user explicitly requests global Codex or global CCE
configuration work.

Do not scan the parent directory of the repository looking for sibling projects.

Do not assume that repositories previously mentioned in another conversation, task, terminal
session, or configuration are relevant to the current repository.

If an active agent session is explicitly working across multiple repositories, each repository must
be handled independently in its own repository context. Cross-repository coordination belongs to
the active agent/session layer, not this repository-local skill.

Information learned from one repository's CCE index must never be copied into another repository's
skill, instructions, index assumptions, or configuration unless the user explicitly requests that
cross-repository operation.

## Instructions

### 1. Check index freshness before the first CCE lookup

Before relying on CCE retrieval for the first time in a task, call the current repository's
`index_status` MCP tool.

If the index is reported as:

- current and healthy: continue using CCE;
- stale: refresh the affected paths before relying on retrieval;
- missing: report the missing index and determine whether initialization is required;
- unavailable: do not use CCE-derived findings as evidence;
- unhealthy or corrupt: diagnose the index before continuing;
- unknown because the status request failed: do not assume the index is current.

A running CCE service alone is not proof that its index is current.

### 2. Do not repeatedly check an unchanged index

After a successful `index_status` check, treat that freshness result as valid until something occurs
that can change indexed repository content.

The index becomes potentially stale after:

- editing an indexed source file;
- creating a new indexed source file;
- deleting an indexed source file;
- renaming or moving an indexed source file;
- applying a patch that modifies source files;
- generating source that is intentionally indexed;
- checking out another branch;
- merging;
- rebasing;
- resetting repository contents;
- pulling repository changes;
- changing CCE ignore configuration;
- changing CCE indexing configuration;
- another process modifying repository source files.

Do not call `index_status` repeatedly between searches when no indexed content has changed.

### 3. Prefer CCE for repository exploration

Use `context_search` as the primary CCE exploration tool.

Use `expand_chunk` only after selecting a relevant search result that needs more surrounding code.

Use `related_context` only when dependency, caller, callee, import, inheritance, or related-code
tracing is needed.

Use the smallest useful retrieval scope.

Do not retrieve large amounts of code merely because CCE can return them.

Do not use broad filesystem scans when CCE can locate the relevant implementation with less context.

### 4. Use direct file reads when the file is already known

CCE is primarily a discovery and retrieval tool.

When a file path is already known and the file is about to be edited, read the relevant file or
relevant section directly rather than repeatedly searching CCE for the same content.

Do not use CCE as an unnecessary extra step for a file that:

- is already known;
- has already been inspected;
- is about to be edited;
- can be verified more accurately from its current filesystem contents.

The filesystem is the source of truth for editing.

The CCE index is a retrieval aid.

### 5. Reindex after an atomic edit batch

After an atomic batch of edits, refresh every changed indexable source file before:

- performing further CCE retrieval that could depend on those changes; or
- declaring the task complete when CCE informed the work.

Reindex every changed source file before continuing with code retrieval or before declaring the task complete.

An atomic edit batch means a logically related set of edits that should be refreshed together before
CCE is queried again.

Examples:

- editing one service and its test;
- changing a Twig partial and its SCSS;
- changing a controller, form type, and related test;
- renaming a class and updating its references.

Do not interrupt every individual keystroke with a reindex.

Finish the logical edit batch, then refresh the changed paths.

### 6. Prefer the current repository's CCE MCP `reindex` tool

When available, prefer the current repository's CCE `reindex` MCP tool for refreshing changed files.

Use path-scoped or incremental operation whenever the MCP interface supports it.

Do not request a full-project refresh when individual changed files can be updated.

Do not reindex unchanged files unnecessarily.

After refreshing the changed paths successfully, call `index_status` once to establish a new known
fresh state.

Never use the CCE MCP server registered for another repository.

