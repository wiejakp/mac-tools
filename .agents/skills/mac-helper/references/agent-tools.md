# Shared skills and local tools

Run `<repository>/agent-setup.sh --share-skills --dry-run` before installation.
`--share-skills --yes` consolidates personal agent skills into `~/.agents/skills`,
leaves compatibility links, preserves Codex `.system`, and saves local backups.
Codex retains per-skill compatibility links under `~/.codex/skills`; Claude Code
and Gemini use `~/.claude/skills` and `~/.gemini/skills` pointing to the library.
Existing name conflicts stop the operation before anything moves. Keep the
repository at its installed location; moving it requires reinstalling its skill link.

CCE is repository-specific. Run `git rev-parse --show-toplevel`, then `cce status`
from that exact root. Use its matching stdio MCP `index_status` and `context_search`
when available. Otherwise `cce search 'local agent setup' --top-k 3` proves local
retrieval without borrowing another project's server. If no index exists, review
secret/ignored-path exclusions, back up configuration, and use `cce init --agent
codex` for Codex. That command registers this root and performs initial indexing;
set `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1` to
prevent downloads during diagnostics. Refresh changes with `cce index --path
<changed-path>`. Do not full-reindex a healthy index or confuse `Transport closed`
with index corruption. New MCP registrations need a fresh client/session.

Context-mode MCP reachability and hook health are independent. Discover the
current client's `ctx_execute`, `ctx_execute_file`, and `ctx_search` capabilities.
Before persistent/file operations, verify that the server's workspace is the
active Git root. If `ctx_execute_file` reports a different project root, stop
using that server's memory/file tools and start a fresh session from the intended
repository. Do not add an allow rule that grants cross-project access to hide the
mismatch. A fresh stdio server launched with that repository as its working
directory can verify the configuration separately from the stale session.
Analyze large data inside the local tool and print bounded results. Runtime-specific
hooks/configuration are separate from the shared skill text. Do not install remote
MCP servers or start hosted Insight for local project analysis.

For `Hook failed: unsupported plugin entry type: .../node_modules/.bin/esbuild`,
inspect that entry with `lstat`. npm symlinks can fail Codex plugin packaging.
Preview `agent-setup.sh --repair-context-mode <exact-plugin-root> --dry-run`.
If still present, `--yes` replaces only internal executable npm links with regular
shell forwarders and backs up their original targets. Reject broken/escaping links.
Do not delete dependencies, disable hooks, erase indexes, or guess an install path.
A plugin update may already have changed the package; inspect again before writing.

Codex also binds hook trust to plugin content. `plugin contents changed; hook
approval required` needs native hook reapproval for the current package. Do not
write invented `trusted_hash` values or bypass approval. Verify native hook
completion after reapproval, plus an MCP call. A successful standalone script or
MCP call alone does not prove Codex hook approval or integration.

Backups live in `~/.agents/backups/` for shared skills/instructions and ignored
`logs/agent-setup-backups/` for npm links. The JSON records every old link target
and move; instruction copies are stored beside the shared-skill manifest. Review
that manifest before a rollback: restore saved instruction copies, replace only
the listed compatibility links, and move shared directories back to their recorded
source paths. Do not overwrite a directory edited after installation. For npm
links, restore only a recorded forwarder to its recorded symlink after confirming
its target still stays inside the same plugin. Reapprove hooks after any rollback.
