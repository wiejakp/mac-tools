# CCE Worktrees, Health, and Safety

## Worktrees require deliberate index handling

Do not accidentally index generated caches or duplicate application trees located inside worktree
storage belonging to the current repository.

If worktrees exist for the current repository, determine whether they are:

- separate CCE project contexts;
- intentionally part of the current index;
- or duplicate working copies that should be excluded from the current index.

Do not inspect unrelated worktrees belonging to another repository.

Do not automatically traverse parent directories looking for worktrees.

Generated cache trees inside worktrees should not enter the primary repository index accidentally.

### 15. Do not reindex unchanged files

Before refreshing paths, use the current repository's edit state to identify what actually changed.

Resolve the repository root:

```sh
repo_root="$(git rev-parse --show-toplevel)"
```

Useful commands include:

```sh
git -C "$repo_root" status --short
git -C "$repo_root" diff --name-only
git -C "$repo_root" diff --cached --name-only
```

Use the smallest appropriate command for the task.

Do not reindex:

- untouched files;
- unrelated files;
- dependency directories;
- generated caches;
- files that CCE deliberately ignores.

### 16. Full-project reindexing is exceptional

A full-project reindex must never be started silently.

A full-project reindex requires an explicit user request unless an approved repository procedure says otherwise.

Prefer incremental repair.

A full-project refresh may be justified when path-scoped or incremental repair is insufficient, such
as:

- index corruption;
- missing or unusable index;
- changed indexing configuration;
- changed ignore configuration requiring broad reconciliation;
- changed embedding/index format;
- repository-wide structural changes;
- a repository-wide branch transition that cannot be reconciled incrementally;
- stale deleted or moved paths that the installed CCE version cannot remove incrementally;
- an explicit user request for a full rebuild.

Before starting a full-project reindex:

1. Determine why incremental repair is insufficient.
2. Confirm that the operation targets only the current repository.
3. Determine the expected scope.
4. Warn that the operation can take substantially longer than path-scoped refreshes.
5. Obtain user approval unless the user already explicitly requested the full reindex.

Never clear or recreate a healthy reusable index merely to refresh a few changed files.

### 17. Preserve the persistent index

Path-scoped updates should modify the existing persistent index for the current repository.

Do not:

- delete the CCE index;
- recreate the index;
- clear the database;
- remove CCE state;
- rerun `cce init`;
- rebuild all embeddings;

merely because one or several source files changed.

Preserve reusable indexed chunks and embeddings whenever possible.

### 18. Avoid concurrent CCE writers for the current repository

Do not intentionally run multiple CCE write operations against the current repository's index at the
same time.

Concurrent writers can cause failures such as:

```text
sqlite3.OperationalError: database is locked
```

The concurrency restriction is repository-scoped.

This skill must not:

- create a global machine-wide CCE lock;
- inspect other repositories merely to coordinate CCE;
- stop CCE processes belonging to unrelated repositories;
- enumerate other CCE project registrations;
- assume another repository's CCE activity conflicts with the current repository.

Before a manual full-project indexing operation, check only whether another writer is targeting the
current repository.

For ordinary path-scoped refreshes, serialize writes for the current repository when necessary.

If a database lock occurs:

1. Resolve the current repository root.
2. Identify active CCE writers targeting that repository only.
3. Determine whether duplicate writers or indexers target the same repository.
4. Stop the conflicting writer when appropriate.
5. Preserve the existing index.
6. Retry the smallest failed operation.

Do not kill unrelated CCE processes.

Do not delete the SQLite/index database as the first response to a lock.

### 19. Do not expose other project configuration while diagnosing CCE

When diagnosing a CCE problem for the current repository, inspect only information needed for the
current repository.

Do not dump the entire global Codex MCP configuration merely to find the current repository's CCE
entry.

Do not print:

- unrelated MCP server names;
- sibling project paths;
- unrelated local filesystem paths;
- unrelated project metadata.

If global configuration must be inspected, filter the output to the current repository whenever
possible.

### 20. CCE service health and index freshness are different states

Keep these concepts separate:

```text
CCE service operational
```

does not necessarily mean:

```text
CCE index current
```

Likewise:

```text
index_status healthy
```

does not replace verification of newly changed source if the index was checked before those changes.

Use service diagnostics for service problems and index freshness checks for retrieval correctness.

### 21. Reindex failure blocks fresh CCE conclusions

If a required refresh fails or times out:

- report the exact failure;
- do not represent the affected path as freshly indexed;
- do not rely on stale CCE results for conclusions about the modified code;
- use the current filesystem directly when work can safely continue without CCE;
- repair CCE separately when necessary.

Do not claim task completion based on stale CCE evidence when CCE retrieval was required for final
verification.

### 22. CCE does not replace code verification

CCE improves discovery and retrieval.

It does not replace:

- reading the final edited source;
- `git diff`;
- syntax checks;
- lint;
- PHPUnit;
- JavaScript tests;
- asset builds;
- browser testing;
- runtime verification;
- repository-specific validation.

Do not treat successful indexing as proof that the code is correct.

