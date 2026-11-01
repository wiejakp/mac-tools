# Local Scripts

Run `make codex` to open Codex's chat list for this repository with automatic
approval review. This uses the same direct Codex command as `~/sites/app_hublist`,
with the workspace-write sandbox, network access, guardian approval, and hooks
enabled. `CODEX` can override the executable, for example `make codex CODEX=/path/to/codex`.

Agent onboarding starts in [AGENTS.md](AGENTS.md) and the [agent guide](docs/agent-guide.md).
The Mac helper files live directly in `.agents/skills/mac-helper` for local
skill discovery. Every change requires a local record, prior-state backup and
explicit rollback steps.

`make agent` starts Cursor Agent; `make gemini` starts Gemini CLI. Both use the
same direct recipes as `app_hublist`. CCE and context-mode are required local
tools for every coding client. See [client installation, usage and hook repair](docs/agent-clients.md)
for prerequisites, project configuration, verification and rollback.

`make clear cache` / `make clear-cache` and `make clear logs` / `make clear-logs`
open the existing cleanup menus and require their normal confirmation. Use
`make preview-cache` or `make preview-logs` for previews. `make mount`,
`make mount-home`, and `make mount-cch` run the corresponding interactive tools.
`make help` lists the shortcuts. No cleanup runs while testing these targets.

For local AI-agent setup, `./agent-setup.sh --help` lists the available repairs.
`./agent-setup.sh --repair-context-mode /absolute/path/to/plugin --dry-run`
previews npm command symlinks that Codex cannot package for hooks. Add `--yes`
to replace them with executable forwarders; original link metadata is saved in
ignored `logs/agent-setup-backups/`. No packages are downloaded or removed.
After a package repair, approve its changed hooks through Codex's native approval
flow. Re-run the preview after a plugin update, since an update may restore npm
symlinks. Exit codes: 0 success, 1 rejected/failed operation, 2 invalid arguments.

`./agent-setup.sh --share-skills --dry-run` previews consolidation of personal
skills into `~/.agents/skills`. Apply with `--yes`. Codex keeps compatibility
links and its managed `.system`; Claude Code and Gemini receive discovery links
to the same library. Existing names that conflict stop the install before any
move. Original instructions and link/move metadata are backed up under
`~/.agents/backups/`. Provider-specific hooks and MCP configuration remain separate.
The portable [Mac helper skill](.agents/skills/mac-helper/SKILL.md) includes local tool
diagnostics and the Superpowers design/plan/execution workflow.

`./agent-setup.sh --inventory` prints sanitized OS, hardware, and relevant agent
availability. Add `--yes` to save ignored `config/mac-helper.local.json`. It does
not collect serial numbers, credentials, network identifiers, or file inventories.

CCE must use this exact Git root. Its initial setup can register local stdio MCP
through `cce init --agent codex`; normal updates use `cce index --path <changed-path>`.
New registrations require a fresh agent session. If context-mode reports another
project root, stop using that server's memory/file tools and restart from this
repository. Do not expand cross-project permissions to mask a stale session.

Personal automation tools with shared code, fixture tests and instructions for AI coding agents. Everything runs locally; no AI service, account, network access or package installation is needed to run the cleaners.

## Available scripts

| Script | Purpose | Report |
| --- | --- | --- |
| `clear-logs.sh` | Remove application runtime logs and rotated `.log` files under `~/sites` | `logs/clear-logs.log` |
| `clear-cache.sh` | Remove known framework and developer tool caches under `~/sites` | `logs/clear-cache.log` |
| `mount.sh` | Mount work and home SMB drives independently, one at a time | On-screen summary |
| `mount-home.sh` | Mount home drives only | On-screen summary |
| `mount-cch.sh` | Mount the CCH work SMB drive only | On-screen summary |

Each script opens a menu when run in Terminal. Choose **1** to clean, **2** to preview or **Q** to quit. Discovery and file activity update one status line in place. The report records every file action and size and appends each run.

All results appear directly in the same Terminal/editor output. After a menu run, the complete before/after/savings summary stays visible, followed by **Press Enter to close this window**. Read the result first, then press Enter when ready. This prevents Finder-launched Terminal windows from disappearing immediately. Explicit `--dry-run` and `--yes` commands return normally without waiting. Vim, vi, Neovim and interactive pagers are prohibited by the project rules.

Previews show a directory table with file counts and total sizes, sorted largest first, followed by the overall total. Loose log files are grouped by their parent directory. There are no file-by-file lists or repeated “would remove” messages in Terminal.

The disk-space summary shows the capacity of the volume containing `~/sites`, used/free space, usage percentages, and selected file data. Previews include estimated savings and projected used/free space after cleanup. Cleanup runs show measured before/after values and a **Space saved** result. A measured decrease in free space is labelled **Free space change**. The summary prints automatically as soon as the operation finishes.

Estimated savings use allocated file blocks, excluding files with shared hard links and files on other volumes. Directory sizes remain logical file sizes, so sparse files can have much smaller estimated savings. APFS snapshots, shared extents, open files and other disk activity can make measured free-space changes differ from the estimate.

Directory tables show only the largest entries, with all other directories included in the totals. Both menu option **2** and `--dry-run` use this view; cleanup uses the same summary after removing files. Detailed reports remain available as optional background diagnostics and are never opened automatically.

```sh
cd ~/Desktop/scripts
./clear-logs.sh                # Interactive menu
./clear-cache.sh              # Interactive menu
./clear-logs.sh --dry-run      # Preview logs
./clear-cache.sh --dry-run     # Preview caches
./clear-logs.sh --yes          # Clean logs without a menu
./clear-cache.sh --yes         # Clean caches without a menu
```

For double-click use in Finder, open **`launchers/Clear Logs.command`** or **`launchers/Clear Cache.command`**. These are standard macOS Terminal launchers for the matching `.sh` tools. The `.sh` files also carry per-file Terminal Open With metadata on this Mac. The menu flows are covered by pseudo-terminal tests. Keep the entry points together with this project; they share the Python engine in `src/`.

## Network drive mounting

```sh
cd ~/Desktop/scripts
./mount.sh                # Work, then home; failures do not stop the other drives
./mount-home.sh           # Home only
./mount-cch.sh            # CCH work drive only
./mount-home.sh --all     # Discover and mount every home disk share after login
./mount.sh --all          # Work plus every discovered home disk share
./mount.sh --dry-run      # Show configured paths without any network access
```

Double-click **`launchers/Mount All.command`**, **`launchers/Mount Home.command`** or **`launchers/Mount CCH.command`** for the same tools in Terminal. After an interactive run the mount summary stays visible until you press Enter to close.

The local configuration is [config/mounts.local.json](config/mounts.local.json), which is ignored by Git and contains no credentials. On this Mac it is preconfigured with the exact work URL and home server `192.168.2.118`. For a new checkout, copy [config/mounts.example.json](config/mounts.example.json) to that local filename and set the addresses.

Home drive names are discovered after login from the server's SMB share catalogue. There is no fixed SSD list or assumed folder prefix. The script displays the advertised disk shares and offers **Mount all** (Enter), selected numbers/ranges such as `1,3-5`, or `0` to skip. `--all` still displays the discovered drives but mounts them without a selection prompt. One home username/password is used for both discovery and all selected home mounts.

Discovery lists SMB exports, not physical disks or folders inside an export. If several disks are only folders inside one advertised share, the script mounts that share; it does not browse inside it to look for more drives. `--dry-run` shows the configured servers without authenticating or discovering live shares.

Each server gets its own username and hidden password prompt. Work usernames can include a domain, for example `DOMAIN\username`. The scripts do not save passwords, put them in command-line arguments, or repeat native error payloads that might contain secrets. Home discovery uses macOS `smbutil` with a private terminal; its password is sent privately to the native prompt. macOS receives mount requests through its built-in mount service.

An unavailable home server is skipped before credentials are requested. The quick CCH reachability check is advisory: it does not block the native macOS SMB mount when a short hostname cannot be confirmed. Enter your work credentials to try, or leave the CCH username blank to skip it and continue with home. Use your work account format, such as `DOMAIN\username` or `username@domain`.

If `cch-fp01` cannot be resolved, run `./mount-cch.sh --cch-server FULL_HOSTNAME_OR_IP` using the address supplied by your work IT team. This changes only the CCH server address; `users%24/Home/pwiejak` and home settings are preserved. The same option works with `mount.sh`.

Mounts run sequentially. Reachability checks default to four seconds, with a separate 35-second limit per mount. Use `--timeout` or `--mount-timeout` to change those limits. `--config` accepts an alternate configuration file inside this project.

These tools only check the SMB port, retrieve share-catalogue metadata and request mounts. They never list files/directories inside a share, open Finder windows or read mounted files. Development tests use simulated servers and dummy credentials; native AppleScript is compiled for syntax verification without executing a real mount. Live discovery/mounting has not been validated against either server.

Network-tool exit status: `0` at least one drive ready and no mount failures (other networks may be skipped), `1` no reachable drives, a failed mount or cancellation, `2` invalid configuration/arguments or missing interactive credential input, `130` an interruption outside a mount attempt. Preview returns `0` for valid configuration and never asks for credentials.

## Cleanup scope

The default root is `~/sites`. Nested applications are recognized from framework entry points and language project manifests. The cleaners do not execute those applications.

- Symfony: `var/cache`, `var/log`, `var/logs`, legacy `app/cache` and `app/logs`.
- Laravel: `storage/logs`, `storage/framework/cache`, compiled views in `storage/framework/views`, and `bootstrap/cache`.
- JavaScript tools: `.next/cache`, `.nuxt/cache`, `.angular/cache`, `.cache`, `.parcel-cache`, `.turbo`, Vite caches and common lint cache files.
- Test/language tools: PHPUnit, pytest, mypy, Ruff and Python `__pycache__` directories.
- Outside excluded locations, log cleanup recognizes `.log` and rotated names such as `.log.1.gz` or `.log-20261021`.

Uploads, databases, sessions, dependencies, Git files, source fixtures, saved test artifacts and temporary worktree copies are preserved. Only `.cache` and `.vite` inside `node_modules` are eligible. Symlinks and cloud-backed paths are skipped. Cache/log root directories and keep files such as `.gitignore` remain in place.

These are allowlisted runtime caches, rather than every directory with “cache” in its name. Global package caches, generated production assets and service memory caches are outside scope. Log mode skips cache trees; cache mode skips log trees. Applications may create new runtime files after cleanup.

Requires macOS and Python 3.9 or newer at `/usr/bin/python3`. Exit status: `0` success or preview complete, `1` cleanup/scan error, `2` invalid arguments or missing explicit noninteractive mode, `130` interrupted.

## Development and agent work

Read [AGENTS.md](AGENTS.md) before changing tools. [Adding scripts](docs/adding-scripts.md) describes how to extend the project.

```sh
make verify
```

Verification checks shell/Python syntax and runs deletion tests in disposable directories inside this repository. It does not clean real applications. Existing personal scripts are preserved and can be incorporated individually.

```text
clear-logs.sh / clear-cache.sh  Public entry points
launchers/                     Double-click macOS Terminal launchers
src/local_scripts/             Reusable implementations
tests/                         Disposable fixture tests
docs/                          Contributor and implementation notes
logs/                          Local reports, ignored by Git
AGENTS.md                      Agent scope, privacy and verification rules
```
