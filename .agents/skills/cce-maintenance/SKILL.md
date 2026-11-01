---
name: cce-maintenance
description: "Use when using, validating, or refreshing the local Code Context Engine."
---

# CCE Maintenance

Use only the Code Context Engine instance tied to the exact current repository, and keep retrieval health separate from index freshness.

## Workflow

1. Resolve the Git root and confirm the matching CCE server before persistent retrieval.
2. Load the references matching the operation below.
3. Prefer path-scoped refreshes after atomic edits; serialize writers and preserve the persistent index.
4. Verify source changes independently of CCE health.

## Reference Routing

- For repository identity, transport/freshness checks, and retrieval selection, read [CCE Repository Isolation and Retrieval](references/isolation-and-retrieval.md).
- For CLI fallback and modified/new/renamed/deleted path refreshes, read [CCE Path Refresh Workflows](references/path-refresh-workflows.md).
- For worktrees, unchanged/generated files, full reindex exceptions, locks, privacy, and failure states, read [CCE Worktrees, Health, and Safety](references/worktrees-health-and-safety.md).
- For operational sequences, quick reference, completion law, and code locations, read [CCE Commands and Completion](references/commands-and-completion.md).

## Verification

Use [evaluation cases](references/evaluation-cases.json) to verify repository isolation, refresh selection, and forbidden cross-project or full-reindex behavior.

## Common Mistakes

- Treating a closed MCP transport as proof that the persistent index is corrupt.
- Reindexing the full repository when changed-path refresh is sufficient.

## Final Verification

Before declaring an implementation task complete, follow the [final verification contract](../skill-validation/references/final-verification.md).
