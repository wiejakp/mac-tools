# CCE Commands and Completion

## Recommended Workflow

### Initial retrieval

```text
resolve current repository
    ↓
index_status
    ↓
context_search
    ↓
expand_chunk if needed
    ↓
related_context if needed
    ↓
identify files
    ↓
read current filesystem source
```

### After source edits

```text
edit atomic source batch
    ↓
identify changed indexable paths in current repository
    ↓
path-scoped CCE refresh
    ↓
index_status
    ↓
resume CCE retrieval if needed
```

### Several changed files

```text
edit A
edit B
edit C
    ↓
refresh A
refresh B
refresh C
    ↓
index_status once
```

Do not:

```text
edit A
    ↓
full-project reindex
    ↓
edit B
    ↓
full-project reindex
```

### Rename

```text
old/path.php
    ↓
rename
    ↓
new/path.php
    ↓
refresh/reconcile current repository state
    ↓
verify old path removed
    ↓
index_status
```

### Delete

```text
delete path.php
    ↓
incremental stale-path reconciliation
    ↓
verify obsolete path removed when relevant
    ↓
index_status
```

### CCE lock

```text
database is locked
    ↓
resolve current repository root
    ↓
find writer targeting current repository only
    ↓
stop conflicting writer if necessary
    ↓
preserve index
    ↓
retry smallest failed update
```

## Quick Reference

| Situation | Required Action |
|---|---|
| First CCE lookup | Resolve current repository, `index_status`, then `context_search` |
| Additional lookup with no edits | Continue searching, do not repeat `index_status` |
| Known file about to be edited | Read the filesystem directly |
| One modified file | Path-scoped refresh, then `index_status` |
| Several modified files | Refresh changed paths only, then one `index_status` |
| New file | Index the new path, then `index_status` |
| Renamed file | Refresh new path and reconcile old path |
| Deleted file | Reconcile stale indexed path, do not index nonexistent path |
| Zero scoped result | Check path, ignore status, repository root, status, and one retrieval |
| CCE service running | Not sufficient proof that the index is fresh |
| Reindex failure | Stop fresh CCE conclusions for affected paths and report the error |
| SQLite lock | Find writer for current repository only, preserve index, retry smallest operation |
| Full-project reindex | Only when incremental repair is insufficient and user has approved |
| No indexed changes | Do not reindex |
| Multiple repositories | Do not enumerate or coordinate them from this repository-local skill |
| Task verification | Use tests, lint, browser, and runtime checks in addition to CCE |

## Common Mistakes

- Hardcoding local repository names or absolute project paths into this skill.
- Mentioning sibling repositories in a repository-local skill.
- Inspecting parent directories to discover other projects.
- Dumping global Codex configuration containing unrelated project paths.
- Searching CCE immediately after editing indexed source without refreshing it.
- Calling `index_status` before every search even though nothing changed.
- Treating an operational CCE service as proof that its index is current.
- Reading entire large files when `context_search` could locate the relevant implementation.
- Searching CCE repeatedly for a known file that is already about to be edited.
- Reindexing unchanged files.
- Running a full-project reindex because one file changed.
- Running a full-project reindex because a path-scoped operation returned zero chunks.
- Clearing a healthy persistent index to refresh ordinary source edits.
- Running `cce init` again merely to update existing source.
- Assuming `cce reindex` exists in the CLI because an MCP `reindex` tool exists.
- Trying to path-index a deleted file.
- Indexing the new side of a rename without checking that the old path was removed.
- Indexing `vendor/`, Symfony cache, logs, generated builds, or duplicate worktree cache trees.
- Running multiple CCE writers against the same repository's SQLite-backed index.
- Killing CCE processes belonging to unrelated repositories.
- Creating a machine-wide lock when only repository-local serialization is needed.
- Treating successful indexing as a replacement for tests.
- Declaring a task complete using stale CCE retrieval.

## Completion Law

When CCE informed a task that changed indexed source:

1. Resolve and remain within the current repository.
2. Identify the final changed indexed paths.
3. Refresh those paths using incremental or path-scoped indexing.
4. Reconcile deleted and renamed paths where applicable.
5. Call `index_status` once after the refresh.
6. If further CCE retrieval is required, use it only after freshness is established.
7. Run the task's actual validation requirements.
8. Do not perform a full-project reindex unless incremental repair was insufficient and the user
   approved the broader operation.
9. Do not inspect, expose, or modify CCE state belonging to unrelated repositories.

A task is not complete merely because CCE accepted a refresh request. The source changes must still
pass the repository's normal validation.

## Code Locations

- CCE MCP tools registered for the current repository
- current repository `AGENTS.md`
- current repository `.gitignore`
- current repository `.git/hooks/`
- current repository `.agents/skills/`

Global configuration may be inspected only when the user explicitly requests global CCE or Codex
configuration work. Do not expose unrelated repository entries when doing so.

## Related

- [Skill Validation](../../skill-validation/SKILL.md)
- [Phpunit Testing](../../phpunit-testing/SKILL.md)
