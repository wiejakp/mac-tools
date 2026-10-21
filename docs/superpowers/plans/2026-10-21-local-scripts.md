# Local Scripts Implementation Plan

**Goal:** Create a local, extensible project at `~/Desktop/scripts` with independent log and cache cleaners for apps under `~/sites`.

**Architecture:** Two shell entry points call one Python standard-library engine. Agent guidance, documentation and fixture tests live in the same Git repository. No remote service or application code is executed.

**Constraints:** Preserve existing personal scripts. Never follow symlinks or access cloud storage. Keep log and cache modes isolated. Preview real applications; test deletions only in disposable repository fixtures.

- [x] Initialize the project on `main`, move the cleanup engine and fixture tests into `src/local_scripts/` and `tests/`, and relocate the whole repository to `~/Desktop/scripts`.
- [x] Add failing isolation tests, implement `--kind logs|cache`, and create executable `clear-logs.sh` and `clear-cache.sh` launchers.
- [x] Add `AGENTS.md`, README, project metadata, a verification command and contributor guidance for future automation scripts.
- [x] Verify tests, shell syntax, interactive menus and real app discovery; configure per-file Terminal metadata and standard macOS click launchers.
