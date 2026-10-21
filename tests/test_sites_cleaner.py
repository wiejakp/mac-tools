#!/usr/bin/python3
"""Cleanup behavior verified only against disposable repository fixtures."""
import importlib.machinery
import importlib.util
from pathlib import Path
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).absolute().parents[1]
SCRIPT = REPO_ROOT / "src/local_scripts/sites_cleaner.py"
loader = importlib.machinery.SourceFileLoader("sites_cleaner", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
cleaner = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = cleaner
loader.exec_module(cleaner)


class CleanerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".clean-sites-test-", dir=REPO_ROOT / "tests")
        self.base = Path(self.temp.name)
        self.root = self.base / "sites"
        self.root.mkdir()
        self.events = []

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, content="test data"):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def run_clean(self, dry_run=False):
        plan = cleaner.build_plan(self.root, self.events.append)
        return cleaner.execute_plan(plan, dry_run, self.events.append)

    def test_framework_caches_logs_and_metadata(self):
        self.put("symfony/bin/console")
        self.put("laravel/artisan")
        deleted = [self.put(n) for n in [
            "symfony/var/cache/dev/container.php", "symfony/var/log/dev.log",
            "symfony/var/log/prod.log.1.gz", "symfony/.phpunit.cache/results",
            "symfony/app/cache/prod/container.php", "symfony/app/logs/old.log",
            "laravel/storage/logs/laravel.log", "laravel/storage/framework/cache/data/key",
            "laravel/storage/framework/views/view.php", "laravel/bootstrap/cache/config.php",
        ]]
        kept = [self.put(n) for n in [
            "symfony/var/cache/.gitignore", "symfony/var/log/.gitkeep",
            "symfony/.env.local", "symfony/src/Cache/Service.php",
            "laravel/storage/framework/sessions/session", "laravel/storage/app/photo.jpg",
            "laravel/bootstrap/cache/.gitignore", "symfony/var/database.sqlite",
        ]]
        stats = self.run_clean()
        self.assertTrue(all(not f.exists() for f in deleted))
        self.assertTrue(all(f.exists() for f in kept))
        self.assertTrue((self.root / "symfony/var/cache").is_dir())
        self.assertEqual(stats.files, len(deleted))
        self.assertEqual(stats.bytes, len(deleted) * len("test data"))
        self.assertEqual(stats.errors, 0)

    def test_dry_run_does_not_mutate(self):
        self.put("app/bin/console")
        target = self.put("app/var/cache/dev/item")
        marker = self.put("app/var/cache/.gitignore")
        before = [(str(p.relative_to(self.root)), p.read_bytes()) for p in self.root.rglob("*") if p.is_file()]
        stats = self.run_clean(True)
        after = [(str(p.relative_to(self.root)), p.read_bytes()) for p in self.root.rglob("*") if p.is_file()]
        self.assertEqual(before, after)
        self.assertTrue(target.exists() and marker.exists())
        self.assertEqual(stats.files, 1)

    def test_nested_apps_node_tool_caches_and_rotated_logs(self):
        self.put("group/my app/package.json", "{}")
        deleted = [self.put(n) for n in [
            "group/my app/.next/cache/key", "group/my app/node_modules/.cache/key",
            "group/my app/node_modules/.vite/key", "group/my app/src/__pycache__/x.pyc",
            "group/my app/.eslintcache", "group/my app/debug.log",
            "group/my app/debug.log.2026-10-20.gz", "group/my app/debug.log-20261020",
        ]]
        kept = [self.put(n) for n in [
            "group/my app/node_modules/dependency/debug.log", "group/my app/vendor/lib/test.log",
            "group/my app/.git/objects/cache.log", "group/my app/uploads/user.log",
            "group/my app/backups/export.log", "group/my app/data/database.log",
            "group/my app/.yarn/cache/package.zip", "group/my app/.next/server/app.js",
        ]]
        stats = self.run_clean()
        self.assertTrue(all(not f.exists() for f in deleted))
        self.assertTrue(all(f.exists() for f in kept))
        self.assertEqual(stats.errors, 0)

    def test_symlinks_and_cloud_named_directories_are_skipped(self):
        outside = self.base / "outside"
        outside.mkdir()
        survivor = outside / "important.log"
        survivor.write_text("keep me")
        self.put("app/bin/console")
        cache = self.put("app/var/cache/local").parent
        (cache / "linked.log").symlink_to(survivor)
        (self.root / "linked-app").symlink_to(outside, target_is_directory=True)
        self.put("app/.next/cache-placeholder")
        (self.root / "app/.next/cache").symlink_to(outside, target_is_directory=True)
        cloud = self.put("app/GoogleDrive/no.log")
        stats = self.run_clean()
        self.assertEqual(survivor.read_text(), "keep me")
        self.assertTrue((cache / "linked.log").is_symlink())
        self.assertTrue(cloud.exists())
        self.assertGreater(stats.skipped, 0)

    def test_symlink_ancestor_swap_cannot_escape_root(self):
        self.put("app/bin/console")
        self.put("app/var/cache/original")
        plan = cleaner.build_plan(self.root, self.events.append)
        moved = self.root / "app/var-real"
        (self.root / "app/var").rename(moved)
        outside = self.base / "outside"
        (outside / "cache").mkdir(parents=True)
        survivor = outside / "cache/important"
        survivor.write_text("keep")
        (self.root / "app/var").symlink_to(outside, target_is_directory=True)
        stats = cleaner.execute_plan(plan, False, self.events.append)
        self.assertTrue(survivor.exists())
        self.assertTrue((moved / "cache/original").exists())
        self.assertGreater(stats.errors + stats.skipped, 0)

    def test_root_identity_change_is_refused(self):
        self.put("app/bin/console")
        self.put("app/var/log/dev.log")
        plan = cleaner.build_plan(self.root, self.events.append)
        self.root.rename(self.base / "old-sites")
        self.root.mkdir()
        survivor = self.put("app/var/log/dev.log")
        with self.assertRaises(cleaner.UnsafePath):
            cleaner.execute_plan(plan, False, self.events.append)
        self.assertTrue(survivor.exists())

    def test_missing_root_and_symlink_root_are_refused(self):
        with self.assertRaises((OSError, cleaner.UnsafePath)):
            cleaner.build_plan(self.base / "missing", self.events.append)
        link = self.base / "linked"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises((OSError, cleaner.UnsafePath)):
            cleaner.build_plan(link, self.events.append)

    def test_app_detection_is_read_only(self):
        self.put("a/bin/console")
        self.put("a/var/log/dev.log")
        self.put("b/artisan")
        self.put("b/storage/logs/dev.log")
        plan = cleaner.build_plan(self.root, self.events.append)
        self.assertEqual(len(plan.apps), 2)
        self.assertEqual(len(plan.targets), 2)
        self.assertTrue((self.root / "a/var/log/dev.log").exists())

    def test_source_fixtures_and_archived_app_copies_are_preserved(self):
        self.put("app/bin/console")
        active = self.put("app/var/log/dev.log")
        kept = [self.put(n) for n in [
            "app/tests/fixtures/example.log", "app/var/tmp/old/bin/console",
            "app/var/tmp/old/var/log/test.log", "app/var/worktrees/copy/bin/console",
            "app/var/worktrees/copy/var/cache/key", "app/var/reports/saved.log",
            "app/var/verification/saved.log", "app/src/.cce/index.log",
        ]]
        plan = cleaner.build_plan(self.root, self.events.append)
        self.assertEqual(plan.apps, {"app"})
        cleaner.execute_plan(plan, False, self.events.append)
        self.assertFalse(active.exists())
        self.assertTrue(all(path.exists() for path in kept))

    def test_a_permission_error_does_not_stop_other_targets(self):
        self.put("app/bin/console")
        denied = self.put("app/var/log/a.log")
        later = self.put("app/var/log/z.log")
        original = os.unlink

        def remove(name, **kwargs):
            if name == "a.log":
                raise PermissionError(13, "Permission denied")
            return original(name, **kwargs)

        with mock.patch.object(cleaner.os, "unlink", side_effect=remove):
            stats = self.run_clean()
        self.assertTrue(denied.exists())
        self.assertFalse(later.exists())
        self.assertEqual(stats.errors, 1)

    def test_log_symlinks_are_refused_and_concurrent_runs_are_locked(self):
        destination = self.base / "important.txt"
        destination.write_text("preserve")
        link = self.base / "linked.log"
        link.symlink_to(destination)
        ui = cleaner.Display()
        with self.assertRaises((OSError, cleaner.UnsafePath)):
            ui.open_log(link)
        self.assertEqual(destination.read_text(), "preserve")
        log = self.base / "run.log"
        other = cleaner.Display()
        try:
            ui.open_log(log)
            with self.assertRaises(cleaner.UnsafePath):
                other.open_log(log)
        finally:
            ui.close()
            other.close()

    def test_unknown_cli_option_fails_without_cleaning(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--kind", "logs", "--invalid-option"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_noninteractive_run_requires_explicit_mode(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--kind", "logs"], input="", capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--dry-run", result.stdout + result.stderr)

    def test_logs_mode_never_removes_cache_contents(self):
        self.put("app/bin/console")
        log = self.put("app/var/log/dev.log")
        cache = self.put("app/var/cache/dev/container.php")
        cached_log = self.put("app/var/cache/dev/example.log")
        plan = cleaner.build_plan(self.root, self.events.append, kind="logs")
        cleaner.execute_plan(plan, False, self.events.append)
        self.assertFalse(log.exists())
        self.assertTrue(cache.exists() and cached_log.exists())

    def test_cache_mode_never_removes_logs(self):
        self.put("app/bin/console")
        log = self.put("app/var/log/dev.log")
        loose_log = self.put("app/debug.log")
        cache = self.put("app/var/cache/dev/container.php")
        plan = cleaner.build_plan(self.root, self.events.append, kind="cache")
        cleaner.execute_plan(plan, False, self.events.append)
        self.assertTrue(log.exists() and loose_log.exists())
        self.assertFalse(cache.exists())

    def test_shell_entry_points_work_from_another_directory(self):
        for name in ("clear-logs.sh", "clear-cache.sh", "launchers/Clear Logs.command", "launchers/Clear Cache.command"):
            with self.subTest(script=name):
                entry = REPO_ROOT / name
                self.assertTrue(os.access(entry, os.X_OK))
                result = subprocess.run([str(entry), "--help"], cwd=REPO_ROOT / "tests", capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--dry-run", result.stdout)
                result = subprocess.run([str(entry)], input="", capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)

    def test_both_interactive_menus_render_and_quit_without_scanning(self):
        entries = (
            ("clear-logs.sh", "LOG CLEANER", "application logs"),
            ("clear-cache.sh", "CACHE CLEANER", "application caches"),
            ("launchers/Clear Logs.command", "LOG CLEANER", "application logs"),
            ("launchers/Clear Cache.command", "CACHE CLEANER", "application caches"),
        )
        for name, title, action in entries:
            with self.subTest(script=name):
                master, slave = pty.openpty()
                child_env = dict(os.environ, TERM="xterm-256color")
                child_env.pop("NO_COLOR", None)
                process = subprocess.Popen([str(REPO_ROOT / name)], stdin=slave, stdout=slave, stderr=slave, env=child_env)
                os.close(slave)
                output = b""
                answered = False
                deadline = time.monotonic() + 5
                try:
                    while time.monotonic() < deadline:
                        if select.select([master], [], [], 0.1)[0]:
                            try:
                                chunk = os.read(master, 8192)
                            except OSError:
                                break
                            if not chunk:
                                break
                            output += chunk
                        if b"Select [1]:" in output and not answered:
                            os.write(master, b"q\n\n")
                            answered = True
                        if process.poll() is not None:
                            break
                    self.assertEqual(process.wait(timeout=1), 0)
                    self.assertIn(title.encode(), output)
                    self.assertIn(action.encode(), output)
                    self.assertIn(b"\x1b[", output)
                    self.assertNotIn(b"Scanning apps", output)
                finally:
                    os.close(master)
                    if process.poll() is None:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    unittest.main(verbosity=2)
