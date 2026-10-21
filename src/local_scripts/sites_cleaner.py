#!/usr/bin/python3
"""Local cleanup engine shared by clear-logs.sh and clear-cache.sh."""
import argparse
from dataclasses import dataclass, field
from datetime import datetime
import fcntl
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time

VERSION = "1.0"
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
KEEP_FILES = {".gitignore", ".gitkeep", ".keep", ".htaccess", "CACHEDIR.TAG"}
PROTECTED_DIRS = {
    ".git", ".hg", ".svn", "vendor", "node_modules", "bower_components",
    ".venv", "venv", "env", ".tox", ".idea", ".vscode", ".yarn", ".pnpm-store",
    "uploads", "upload", "backups", "backup", "data", "database", "databases",
    "sessions", "session", "site-packages", "lost+found",
    ".cce", ".codex", ".claude", ".agents", ".context-mode",
}
NAMED_CACHES = {
    ".cache", ".phpunit.cache", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".sass-cache", ".parcel-cache", ".rollup.cache", ".turbo", ".vite",
    ".vite-temp", "__pycache__",
}
FILE_CACHES = {
    ".phpunit.result.cache", ".php-cs-fixer.cache", ".php_cs.cache",
    ".eslintcache", ".stylelintcache",
}
APP_CACHE_PATHS = {
    "var/cache", "app/cache", ".next/cache", ".nuxt/cache", ".angular/cache",
    "storage/framework/cache", "storage/framework/views", "bootstrap/cache",
}
APP_LOG_PATHS = {"var/log", "var/logs", "app/logs", "storage/logs", "logs", "log"}
SOURCE_FIXTURE_DIRS = {"test", "tests", "spec", "specs", "fixtures", "__tests__"}
APP_PRESERVED_PATHS = {
    "storage/app", "var/tmp", "var/temp", "var/worktrees", "var/reports",
    "var/verification", "var/test", "var/tests", "var/artifacts",
    "worktrees", ".worktrees",
}
APP_MARKERS = {
    "composer.json", "package.json", "artisan", "manage.py", "pyproject.toml",
    "requirements.txt", "Gemfile", "go.mod", "Cargo.toml",
}
LOG_PATTERN = re.compile(r"\.log(?:[.-].+)?$", re.IGNORECASE)
CLOUD_NAMES = (
    "googledrive", "google drive", "onedrive", "sharepoint", "dropbox",
    "icloud", "cloudstorage", "mobile documents",
)


class UnsafePath(Exception):
    pass


@dataclass
class Target:
    relative: str
    kind: str
    app: str
    directory: bool


@dataclass
class Plan:
    root: Path
    identity: tuple
    targets: list = field(default_factory=list)
    apps: set = field(default_factory=set)
    skipped: int = 0
    errors: int = 0


@dataclass
class Stats:
    files: int = 0
    bytes: int = 0
    directories: int = 0
    skipped: int = 0
    errors: int = 0


def event(report, level, message):
    report({"level": level, "message": str(message)})


def cloud_name(name):
    return name.casefold() == "box" or any(word in name.casefold() for word in CLOUD_NAMES)


def protected_directory(name):
    return name.casefold() in PROTECTED_DIRS or cloud_name(name)


def keep_file(name):
    return name in KEEP_FILES or name.casefold().startswith(".env")


def open_directory(path):
    """Open every ancestor without following any symbolic link."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    if any(cloud_name(part) for part in absolute.parts):
        raise UnsafePath("Cloud-backed paths are excluded.")
    fd = os.open(absolute.anchor, DIRECTORY_FLAGS)
    try:
        for component in absolute.parts[1:]:
            child = os.open(component, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def identity(fd):
    info = os.fstat(fd)
    return info.st_dev, info.st_ino


def build_plan(root, report, kind="all"):
    if kind not in ("all", "logs", "cache"):
        raise ValueError("Unknown cleanup kind: " + kind)
    root = Path(os.path.abspath(os.fspath(root)))
    fd = open_directory(root)
    try:
        plan = Plan(root, identity(fd))
    finally:
        os.close(fd)
    app_roots = set()
    seen = set()

    def add(path, target_kind, app, directory=True):
        if kind != "all" and target_kind != ("LOGS" if kind == "logs" else "CACHE"):
            return
        relative = path.relative_to(root).as_posix()
        if relative not in seen:
            seen.add(relative)
            plan.targets.append(Target(relative, target_kind, app, directory))

    def scan_error(error):
        plan.errors += 1
        event(report, "ERROR", "Cannot scan: {}".format(error))

    for current, directories, files in os.walk(root, topdown=True, followlinks=False, onerror=scan_error):
        current = Path(current)
        directories.sort()
        files.sort()
        regular_markers = [name for name in files if name in APP_MARKERS and not (current / name).is_symlink()]
        console = current / "bin"
        has_console = not console.is_symlink() and (console / "console").is_file() and not (console / "console").is_symlink()
        if regular_markers or has_console:
            app_roots.add(current)
            app_name = current.relative_to(root).as_posix()
            plan.apps.add(app_name)
            event(report, "APP", app_name)
        ancestor = current
        while ancestor != root and ancestor not in app_roots:
            ancestor = ancestor.parent
        app_root = ancestor if ancestor in app_roots else None
        app_name = app_root.relative_to(root).as_posix() if app_root else current.relative_to(root).parts[:1]
        if not isinstance(app_name, str):
            app_name = app_name[0] if app_name else "."

        for name in directories[:]:
            child = current / name
            relative = child.relative_to(app_root).as_posix() if app_root else ""
            if child.is_symlink() or cloud_name(name):
                directories.remove(name)
                plan.skipped += 1
                event(report, "SKIP", "Link or excluded path: " + child.relative_to(root).as_posix())
                continue
            saved_source = app_root and (relative in APP_PRESERVED_PATHS or name in SOURCE_FIXTURE_DIRS)
            if protected_directory(name) or saved_source:
                directories.remove(name)
                # Inspect only these two disposable caches inside dependencies.
                if name == "node_modules":
                    for cache in (".cache", ".vite"):
                        candidate = child / cache
                        try:
                            info = candidate.lstat()
                            if stat.S_ISDIR(info.st_mode):
                                add(candidate, "CACHE", app_name)
                            elif stat.S_ISLNK(info.st_mode):
                                plan.skipped += 1
                        except FileNotFoundError:
                            pass
                        except OSError as error:
                            scan_error(error)
                continue
            target_kind = "CACHE" if name in NAMED_CACHES or relative in APP_CACHE_PATHS else None
            if relative in APP_LOG_PATHS:
                target_kind = "LOGS"
            if target_kind:
                add(child, target_kind, app_name)
                directories.remove(name)
        for name in files:
            child = current / name
            if keep_file(name) or child.is_symlink():
                continue
            if name in FILE_CACHES:
                add(child, "CACHE", app_name, False)
            elif LOG_PATTERN.search(name):
                add(child, "LOGS", app_name, False)
    plan.targets.sort(key=lambda target: (target.app, target.relative))
    return plan


def execute_plan(plan, dry_run, report):
    stats = Stats(skipped=plan.skipped, errors=plan.errors)
    root_fd = open_directory(plan.root)
    try:
        if identity(root_fd) != plan.identity:
            raise UnsafePath("The sites directory changed after scanning. Run again.")

        def problem(relative, error):
            if isinstance(error, FileNotFoundError):
                return
            stats.errors += 1
            event(report, "ERROR", "{}: {}".format(relative, error.strerror or str(error)))

        def remove_file(parent_fd, name, relative, info):
            if dry_run:
                action = "WOULD REMOVE"
            else:
                os.unlink(name, dir_fd=parent_fd)
                action = "REMOVE"
            stats.files += 1
            stats.bytes += info.st_size
            event(report, action, "{}  ({})".format(relative, human_size(info.st_size)))

        def empty_directory(directory_fd, relative):
            empty = True
            for name in sorted(os.listdir(directory_fd)):
                child_relative = relative + "/" + name
                try:
                    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    # Laravel's cache/data is disposable; ordinary app data is
                    # excluded during discovery, before any cache is selected.
                    protected = protected_directory(name) and name.casefold() != "data"
                    if stat.S_ISLNK(info.st_mode) or keep_file(name) or protected:
                        stats.skipped += 1
                        empty = False
                        event(report, "KEEP", child_relative)
                    elif stat.S_ISDIR(info.st_mode):
                        child_fd = os.open(name, DIRECTORY_FLAGS, dir_fd=directory_fd)
                        try:
                            child_empty = empty_directory(child_fd, child_relative)
                        finally:
                            os.close(child_fd)
                        if child_empty:
                            if not dry_run:
                                os.rmdir(name, dir_fd=directory_fd)
                            stats.directories += 1
                        else:
                            empty = False
                    elif stat.S_ISREG(info.st_mode):
                        remove_file(directory_fd, name, child_relative, info)
                    else:
                        stats.skipped += 1
                        empty = False
                        event(report, "KEEP", "Special file: " + child_relative)
                except OSError as error:
                    problem(child_relative, error)
                    if not isinstance(error, FileNotFoundError):
                        empty = False
            return empty

        for number, target in enumerate(plan.targets, 1):
            before_files, before_bytes = stats.files, stats.bytes
            event(report, "TARGET", "[{}/{}] {}  {}".format(number, len(plan.targets), target.kind, target.relative))
            parent_fd = os.dup(root_fd)
            try:
                components = Path(target.relative).parts
                if not components or any(part in (".", "..") or cloud_name(part) for part in components):
                    raise UnsafePath("Invalid cleanup target: " + target.relative)
                for component in components[:-1]:
                    child_fd = os.open(component, DIRECTORY_FLAGS, dir_fd=parent_fd)
                    os.close(parent_fd)
                    parent_fd = child_fd
                name = components[-1]
                info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    stats.skipped += 1
                    event(report, "KEEP", "Symbolic link: " + target.relative)
                elif target.directory and stat.S_ISDIR(info.st_mode):
                    directory_fd = os.open(name, DIRECTORY_FLAGS, dir_fd=parent_fd)
                    try:
                        empty_directory(directory_fd, target.relative)
                    finally:
                        os.close(directory_fd)
                elif not target.directory and stat.S_ISREG(info.st_mode):
                    remove_file(parent_fd, name, target.relative, info)
                else:
                    stats.skipped += 1
                    event(report, "KEEP", "Changed file type: " + target.relative)
            except OSError as error:
                problem(target.relative, error)
            finally:
                os.close(parent_fd)
            event(report, "DONE", "{} files / {}{}".format(stats.files - before_files, human_size(stats.bytes - before_bytes), " planned" if dry_run else " removed"))
    finally:
        os.close(root_fd)
    return stats


def human_size(size):
    amount = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return "{} {}".format(int(amount) if unit == "B" else "{:.1f}".format(amount), unit)
        amount /= 1024


def printable(value):
    return "".join(char if char.isprintable() else "\\x{:02x}".format(ord(char)) for char in str(value))


class Display:
    COLORS = {"APP": "36", "TARGET": "1;36", "DONE": "32", "ERROR": "31", "SKIP": "33", "KEEP": "90", "REMOVE": "90", "WOULD REMOVE": "90", "INFO": "37"}

    def __init__(self):
        self.color = sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
        self.log = None
        self.progress_at = 0.0
        self.progress_visible = False
        self.file_events = 0

    def paint(self, text, color):
        return "\033[{}m{}\033[0m".format(color, text) if self.color else text

    def clear_progress(self):
        if self.progress_visible:
            sys.stdout.write("\r\033[2K")
            self.progress_visible = False

    def open_log(self, path):
        parent_fd = open_directory(path.parent)
        fd = None
        try:
            fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent_fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise UnsafePath("Run log must be a regular file.")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise UnsafePath("Another cleaner is already running. Close it first.")
            self.log = os.fdopen(fd, "a", encoding="utf-8", buffering=1)
            fd = None
            self.write_log("\n=== SITES CLEANER {} | {} ===\n".format(VERSION, datetime.now().isoformat(timespec="seconds")))
        finally:
            os.close(parent_fd)
            if fd is not None:
                os.close(fd)

    def write_log(self, text):
        if self.log:
            try:
                self.log.write(text)
            except OSError:
                # Let main report the failure without retrying a broken log.
                try:
                    self.log.close()
                except OSError:
                    pass
                self.log = None
                raise

    def __call__(self, record):
        level, message = record["level"], printable(record["message"])
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write_log("{} {:<12} {}\n".format(timestamp, level, message))
        # Every file goes to the report; Terminal stays readable and responsive.
        if level in ("REMOVE", "WOULD REMOVE") and self.color:
            self.file_events += 1
            now = time.monotonic()
            if now - self.progress_at < 0.08:
                return
            self.progress_at = now
            columns = max(40, shutil.get_terminal_size((100, 30)).columns - 2)
            text = "  {} files processed  ·  {}".format(self.file_events, message)
            self.clear_progress()
            sys.stdout.write(self.paint(text[:columns], "90") + "\r")
            sys.stdout.flush()
            self.progress_visible = True
            return
        self.clear_progress()
        label = self.paint("{:<12}".format(level), self.COLORS.get(level, "37"))
        print("  {}  {}  {}".format(self.paint(timestamp, "90"), label, message), flush=True)

    def banner(self, root, kind):
        print()
        print(self.paint("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "36"))
        title = "LOG CLEANER" if kind == "logs" else "CACHE CLEANER"
        subtitle = "Application logs and rotated log files" if kind == "logs" else "Framework caches and developer tool caches"
        print(self.paint("  " + title, "1;37") + self.paint("  /  LOCAL APP MAINTENANCE", "90"))
        print("  " + subtitle)
        print(self.paint("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "36"))
        print("  Scope: {}".format(printable(root)))
        print("  Preserves uploads, databases, sessions, dependencies and Git.")
        print("  Saved test artifacts, source fixtures and worktrees are excluded.")
        print("  Symlinks and cloud-backed paths are skipped.\n")

    def close(self):
        self.clear_progress()
        if self.log:
            self.log.close()


def main():
    parser = argparse.ArgumentParser(description="Clean application logs or regenerable caches under ~/sites.")
    parser.add_argument("--kind", choices=("logs", "cache"), required=True, help=argparse.SUPPRESS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true", help="preview without changing application files")
    modes.add_argument("--yes", action="store_true", help="clean immediately without the menu")
    parser.add_argument("--version", action="version", version="Sites Cleaner " + VERSION)
    args = parser.parse_args()
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    pause = interactive and not (args.dry_run or args.yes)
    ui = Display()
    root = Path.home() / "sites"
    ui.banner(root, args.kind)
    description = "application logs" if args.kind == "logs" else "application caches"
    started = time.monotonic()
    status = 0
    try:
        if not args.dry_run and not args.yes:
            if not interactive:
                print("Use --dry-run to preview or --yes to clean from a script.")
                return 2
            print("  [1] Clean " + description)
            print("  [2] Preview only")
            print("  [Q] Quit\n")
            while True:
                choice = input("  Select [1]: ").strip().casefold() or "1"
                if choice in ("q", "quit"):
                    return 0
                if choice in ("1", "2"):
                    args.dry_run = choice == "2"
                    break
                print("  Enter 1, 2, or Q.")
        project_root = Path(os.path.abspath(__file__)).parents[2]
        report_path = project_root / "logs" / ("clear-" + args.kind + ".log")
        ui.open_log(report_path)
        mode = "PREVIEW — application files will stay unchanged" if args.dry_run else "CLEAN — removing " + description
        ui({"level": "INFO", "message": mode})
        ui({"level": "INFO", "message": "Full activity log: " + str(report_path)})
        ui({"level": "INFO", "message": "Scanning apps and cache locations…"})
        plan = build_plan(root, ui, kind=args.kind)
        ui({"level": "INFO", "message": "{} apps found · {} cleanup locations".format(len(plan.apps), len(plan.targets))})
        stats = execute_plan(plan, args.dry_run, ui)
        ui.clear_progress()
        print()
        title = "PREVIEW COMPLETE" if args.dry_run else "CLEANUP COMPLETE"
        if stats.errors:
            title = "PREVIEW FINISHED WITH ERRORS" if args.dry_run else "CLEANUP FINISHED WITH ERRORS"
        print(ui.paint("  " + title, "1;33" if stats.errors else "1;32"))
        summary = "{} files {} · {} file data · {:.1f}s · {} errors".format(stats.files, "would be removed" if args.dry_run else "removed", human_size(stats.bytes), time.monotonic() - started, stats.errors)
        ui({"level": "INFO", "message": summary})
        ui({"level": "INFO", "message": "{} links / protected items skipped. Cache roots and keep files retained.".format(stats.skipped)})
        print("  Full report: {}\n".format(printable(report_path)))
        status = 1 if stats.errors else 0
    except KeyboardInterrupt:
        ui({"level": "INFO", "message": "Stopped. Completed deletions are recorded in the activity log."})
        status = 130
    except (OSError, UnsafePath) as error:
        ui({"level": "ERROR", "message": str(error)})
        status = 1
    finally:
        ui.close()
        if pause:
            try:
                input("  Press Return to finish… ")
            except (EOFError, KeyboardInterrupt):
                pass
    return status


if __name__ == "__main__":
    sys.exit(main())
