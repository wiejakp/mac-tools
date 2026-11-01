# CCE Path Refresh Workflows

## CLI fallback

If the CCE MCP reindex tool is unavailable, broken, or inappropriate for the operation, use the
path-scoped CLI command supported by the installed CCE version.

The currently installed CLI supports:

```sh
cce index --path <absolute-file>
```

Resolve the current repository root dynamically:

```sh
repo_root="$(git rev-parse --show-toplevel)"
```

Use an absolute path to an existing file inside that repository.

Example using a repository-relative changed file:

```sh
repo_root="$(git rev-parse --show-toplevel)"
file="src/Service/ExampleService.php"

cce index --path "$repo_root/$file"
```

Do not assume that an MCP tool name is also a valid CLI command.

In particular, do not run:

```sh
cce reindex
```

unless the installed CLI explicitly exposes that command.

If CLI capabilities are uncertain, inspect the installed version first:

```sh
cce --help
```

or the appropriate command-specific help.

Do not invent CCE commands.

### 8. Modified files use path-scoped refreshes

For ordinary modified files:

1. Finish the atomic edit batch.
2. Collect the changed indexable source paths.
3. Resolve them against the current repository root.
4. Refresh only those paths.
5. Avoid reindexing unchanged files.
6. Call `index_status` once after the refresh.
7. Resume CCE retrieval only when freshness is established.

Example:

```text
Edit:
    src/Service/FooService.php
    tests/phpunit/Service/FooServiceTest.php

Refresh:
    FooService.php
    FooServiceTest.php

Do not:
    rebuild the entire repository index
```

### 9. New files use path-scoped refreshes

New source files that should participate in CCE retrieval must be indexed after creation.

Verify that the new path:

- exists;
- is inside the current repository;
- is not ignored by CCE;
- is an indexable file type.

Then refresh the new path using the current repository's CCE MCP `reindex` tool or the supported
path-scoped CLI command.

### 10. Renamed and moved files require stale-path handling

A rename or move consists of two index concerns:

```text
old/path/File.php
    must no longer appear as current code

new/path/File.php
    must become available at its new path
```

Do not assume that indexing the new path automatically removes the old indexed path.

For renamed or moved files:

1. Use only the current repository's CCE index.
2. Prefer the CCE MCP `reindex` or incremental repository mechanism if it reconciles repository state.
3. Refresh the new path.
4. Ensure the obsolete path is removed or reconciled by the supported CCE mechanism.
5. Call `index_status`.
6. Perform one targeted lookup when necessary to confirm that the obsolete path is no longer returned.

Do not launch a full-project rebuild solely because one file was renamed unless incremental
reconciliation cannot remove the stale path.

### 11. Deleted files cannot be path-indexed directly

A deleted file no longer has an existing absolute path.

Do not attempt:

```sh
cce index --path /path/to/file-that-no-longer-exists.php
```

as though it were an ordinary modified file.

For deleted files:

1. Use the current repository's CCE MCP or incremental repository mechanism that reconciles deleted
   repository paths.
2. Verify with `index_status`.
3. When the deleted file previously mattered to retrieval, perform one targeted lookup to confirm
   that the obsolete path is no longer returned.

If the installed CCE version cannot remove the stale path incrementally, report that limitation and
determine the smallest supported repair.

Do not silently trigger a full-project rebuild.

### 12. Handle zero-file or zero-chunk scoped results conservatively

A path-scoped refresh that reports zero files or zero chunks is not automatically a reason to rebuild
the entire index.

It may mean:

- the file is already current;
- the file contains no indexable chunks;
- the path is ignored;
- the path is outside the current repository;
- the path is incorrect;
- the file type is unsupported;
- the CCE daemon is using another project root;
- the CLI and MCP are targeting different project indexes;
- an operational problem prevented the refresh.

When a scoped update returns zero:

1. Resolve the current repository root.
2. Verify that the path is absolute.
3. Verify that the path exists when it is expected to exist.
4. Verify that it belongs to the current repository.
5. Check whether the path is ignored.
6. Call `index_status`.
7. Perform one known-symbol or known-path retrieval check when useful.
8. Preserve and report the actual result if freshness cannot be established.

Do not automatically launch a full-project reindex because a scoped operation returned zero files
or chunks.

Do not automatically launch a full-project reindex merely because a path-scoped request reports zero files or zero chunks.
The persistent index may already be current; confirm freshness before choosing another repair action.

### 13. Keep generated content out of the index

Do not intentionally index generated, cached, vendor, build, or transient content unless the
repository has a specific reason to search it.

Typical Symfony exclusions include:

```text
vendor/
var/cache/
var/log/
node_modules/
public/build/
coverage/
```

Repository-specific generated directories should also be excluded.

Do not index Symfony-generated cache files such as:

```text
var/cache/*/url_matching_routes.php
```

when the real source is available elsewhere.

Generated files add indexing time, index size, retrieval noise, and parser failures without improving
source-code understanding.

