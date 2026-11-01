# Testing, Planning, and Completion

Identify the smallest meaningful check for changed behavior. Use disposable
fixtures under `tests/`; simulate every SMB connection, catalogue and mount.
Never run cleanup on live applications merely to verify an implementation.

Run focused unittest discovery during implementation, then run `make verify`
once the source, configuration and focused checks are final. Serialize tests that
share state. The main agent owns the final result; two independent full-suite
workers are not required by this project.

For every task, save a change record before mutation. Capture exact original
bytes, modes and absent paths, then document guarded step-by-step rollback.
Preserve unrelated work. Use the user's already-granted implementation authority
rather than requesting duplicate scope approval.

If a check fails, preserve the complete failure set locally, investigate the
affected tests and repair known failures before repeating broad verification.
Do not hide failures, skip cases or weaken checks to obtain a green result.

Report exact commands, exit status and limits. Fixture success is distinct from
native client startup, hook trust, MCP connectivity and live behavior. A later
executable correction invalidates earlier proof for the affected checks.
