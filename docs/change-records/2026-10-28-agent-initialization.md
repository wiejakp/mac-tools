# Repository agent initialization — 2026-10-28

## Purpose and scope

Initialize the existing agentic coding and macOS guidance for this repository:
document its purpose, move its existing Mac helper into native local skill
discovery, and define the coding workflow. Scope is `/Users/pwiejak/Desktop/tools`.
Use the already-installed shared skill library by name. Keep the direct
`make codex` command and existing runtime tools unchanged.

The task adds documentation and physically relocates the existing skill. It does
not install packages, modify global agent settings, approve hooks, register MCP
servers, start background services, inspect credentials or access cloud storage.
Private information remains local except for the user's active Codex service.
Additional transfers require explicit destination-specific permission.

## Planned actions, in order

1. Verify the Git root and existing agent instructions, Mac helper and commands.
2. Create this record before implementation; capture exact bytes, file modes and
   absent-path markers in ignored local recovery data before other changes.
3. Add purpose and session-start guidance to `AGENTS.md`; link the guide in README.
4. Write `docs/agent-guide.md` with purpose, source map, skill selection, macOS
   limits, native commands, verification and recovery rules.
5. Remove the discovery link created in the initial attempt. Move the actual
   `skills/mac-helper` directory to `.agents/skills/mac-helper`; update the setup
   implementation and fixture paths to use the new physical location. The final
   skill directory and its contents must not be symlinks.
6. Verify the link and documentation, run `make verify`, record actual results and
   save final file hashes and modes. Exercise rollback in disposable fixtures.

## Exact affected paths

- Existing files: `AGENTS.md`, `README.md`, `src/local_scripts/agent_setup.py`,
  `tests/test_agent_setup.py`.
- New files: `docs/agent-guide.md`, this record.
- New directories: `.agents`, `.agents/skills`.
- Moved directory and five source/reference files: `skills/mac-helper` to
  `.agents/skills/mac-helper`.
- Local recovery artifacts retained under
  `logs/change-backups/2026-10-28-agent-initialization/`.

Unrelated working-tree changes and the existing Mac helper contents are preserved.
The local link was created, then replaced with a physical move at the user's
direction. Original skill contents, directory modes and setup/test files were
added to the recovery archive before relocating or editing them.
Recovery archives contain only the named repository files; never add secret files.

## Verification and completion

Status: complete within this repository.

- `AGENTS.md` now states the project purpose and session-start workflow;
  `docs/agent-guide.md` documents skills, commands, boundaries and recovery.
- `.agents/skills/mac-helper` is a physical directory. All five original source
  and reference files match their saved bytes; `skills/mac-helper` is absent.
- The setup implementation and its fixture use the new physical location. The
  relocation regression failed against the old source path, then passed after
  the one-line implementation update.
- `make verify` passed: all 79 tests and shell/Python syntax checks passed.
  The run used native macOS compile access; mounts and cleanup stayed simulated.
- Current documentation links resolve and `git diff --check` passed.
- The documented rollback passed in five disposable repositories: full recovery
  restored original bytes, file/directory modes and the old skill location;
  later text edits, changed permissions, symlinks and unexpected directory entries
  were each refused before any mutation. Disposable fixtures were removed.
- Original bytes, permissions and absent paths were captured before their
  implementation changes. `before.json` and `after.json` remain local and ignored.

Codex protects the project's `.agents` configuration directory, so its creation
and the physical move used approved native operations for that exact local path.
Global configuration and shared-library paths were not changed. CLI startup,
current-session skill-catalog refresh, hook trust, MCP transport and CCE index
health were not tested by this documentation/relocation task. CCE/context-mode
access approvals were not requested.

## Step-by-step rollback

1. Stop editing the affected files. Open a terminal in
   `/Users/pwiejak/Desktop/tools`.
2. Keep the ignored recovery directory; it holds exact original bytes and modes
   in `before.json`. `after.json` holds the completed state and archive checksum.
3. Run the following block. It checks every affected path before writing,
   rejects changed files, symlinks or unexpected directory entries. A failed
   preflight makes no changes. Review later edits
   rather than removing these checks.

```sh
/usr/bin/python3 -B - <<'PY'
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

root = Path('/Users/pwiejak/Desktop/tools')
actual = subprocess.check_output(
    ['git', 'rev-parse', '--show-toplevel'], cwd=root, text=True).strip()
if actual != str(root) or root.is_symlink():
    raise SystemExit('Wrong repository; nothing changed')
backup = root / 'logs/change-backups/2026-10-28-agent-initialization'
for path in (root / 'logs', root / 'logs/change-backups', backup,
             backup / 'before.json', backup / 'after.json'):
    if path.is_symlink():
        raise SystemExit('Symlinked recovery path; nothing changed')
raw = (backup / 'before.json').read_bytes()
after = json.loads((backup / 'after.json').read_text())
if hashlib.sha256(raw).hexdigest() != after['before_sha256']:
    raise SystemExit('Recovery archive changed; nothing changed')
before = json.loads(raw)['before']
if set(before) != set(after['paths']):
    raise SystemExit('Recovery paths differ; nothing changed')

def describe(path):
    if path.is_symlink():
        return {'kind': 'symlink', 'target': os.readlink(path)}
    if not path.exists():
        return {'kind': 'absent'}
    mode = stat.S_IMODE(path.stat().st_mode)
    if path.is_file():
        return {'kind': 'file', 'mode': mode,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    if path.is_dir():
        return {'kind': 'directory', 'mode': mode,
                'entries': sorted(child.name for child in path.iterdir())}
    raise SystemExit('Unexpected file type; nothing changed')

for name, expected in after['paths'].items():
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise SystemExit('Invalid path; nothing changed')
    path = root / relative
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise SystemExit('Symlinked parent; nothing changed: ' + name)
    if describe(path) != expected:
        raise SystemExit('Later change found; nothing changed: ' + name)
for entry in before.values():
    if entry['kind'] == 'file':
        base64.b64decode(entry['content_base64'], validate=True)
    elif entry['kind'] not in ('absent', 'directory'):
        raise SystemExit('Unsupported recovery entry; nothing changed')

for name in sorted(before, key=lambda value: len(Path(value).parts), reverse=True):
    path = root / name
    entry = before[name]
    if entry['kind'] == 'absent':
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
for name in sorted(before, key=lambda value: len(Path(value).parts)):
    entry = before[name]
    if entry['kind'] == 'directory':
        path = root / name
        path.mkdir(exist_ok=True)
        path.chmod(entry['mode'])
for name, entry in before.items():
    if entry['kind'] == 'file':
        path = root / name
        path.write_bytes(base64.b64decode(entry['content_base64'], validate=True))
        path.chmod(entry['mode'])
print('Original bytes and permissions restored; new paths removed; backups retained.')
PY
```

4. Run `git --no-pager diff -- AGENTS.md README.md` and confirm only the
   pre-existing changes remain. `make -n codex` must still use the direct native
   recipe. The skill source must be back under `skills/mac-helper`, with its
   original bytes and modes, and the project-local discovery directories removed.
5. Run `make verify` and record its actual outcome. The rollback retains its
   recovery directory and removes this newly created record with the other new
   paths. It never changes global tools or permissions.
