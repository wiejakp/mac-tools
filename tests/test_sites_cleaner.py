#!/usr/bin/python3
"""Cleanup behavior verified only against disposable repository fixtures."""
import importlib.machinery
import importlib.util
import io
from contextlib import redirect_stdout
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

    def test_space_estimate_uses_allocated_blocks_and_excludes_shared_links(self):
        self.put("app/bin/console")
        examples = {}
        for kind, directory, extension in (("logs", "var/log", ".log"), ("cache", "var/cache/dev", ".php")):
            ordinary = self.put("app/{}/ordinary{}".format(directory, extension), "x" * 4096)
            sparse = self.put("app/{}/sparse{}".format(directory, extension), "")
            with sparse.open("wb") as stream:
                stream.truncate(1024 * 1024)
            shared = self.put("app/{}/shared{}".format(directory, extension), "shared")
            survivor = self.base / ("kept-" + kind)
            os.link(shared, survivor)
            examples[kind] = (ordinary, sparse, shared, survivor)
        for kind, (ordinary, sparse, shared, survivor) in examples.items():
            with self.subTest(kind=kind):
                plan = cleaner.build_plan(self.root, self.events.append, kind=kind)
                stats = cleaner.execute_plan(plan, True, self.events.append)
                self.assertEqual(stats.bytes, 4096 + 1024 * 1024 + len("shared"))
                self.assertEqual(stats.reclaimable_bytes, (ordinary.stat().st_blocks + sparse.stat().st_blocks) * 512)
                self.assertTrue(all(path.exists() for path in (ordinary, sparse, shared, survivor)))

    def test_disk_measurement_uses_safe_root_and_skips_symlinks(self):
        usage = cleaner.read_disk_usage(self.root)
        self.assertGreater(usage.total, 0)
        self.assertGreaterEqual(usage.free, 0)
        link = self.base / "linked-sites"
        link.symlink_to(self.root, target_is_directory=True)
        self.assertIsNone(cleaner.read_disk_usage(link))
        self.assertIsNone(cleaner.read_disk_usage(self.base / "missing"))

    def test_preview_disk_summary_compares_current_and_estimated_usage(self):
        gib = 1024 ** 3
        before = cleaner.DiskSpace(1024 * gib, 768 * gib, 256 * gib)
        stats = cleaner.Stats(bytes=32 * gib, reclaimable_bytes=16 * gib)
        ui = cleaner.Display()
        ui.log = io.StringIO()
        output = io.StringIO()
        with redirect_stdout(output):
            ui.show_disk_summary(before, stats, True)
        text = output.getvalue()
        for value in ("DISK SPACE", "NOW", "AFTER (EST.)", "768.0 GiB (75.0%)", "752.0 GiB (73.4%)", "256.0 GiB", "272.0 GiB", "File data selected", "32.0 GiB", "Estimated savings", "16.0 GiB"):
            self.assertIn(value, text)
        self.assertIn("DISK SPACE", ui.log.getvalue())
        self.assertLessEqual(len(text.splitlines()), 10)
        ui.close()

    def test_cleanup_disk_summary_reports_measured_signed_change(self):
        gib = 1024 ** 3
        before = cleaner.DiskSpace(1024 * gib, 512 * gib, 512 * gib)
        for free, expected, label in ((513 * gib, "+1.0 GiB", "Space saved"), (511 * gib, "-1.0 GiB", "Free space change")):
            with self.subTest(change=expected):
                after = cleaner.DiskSpace(1024 * gib, 1024 * gib - free, free)
                ui = cleaner.Display()
                output = io.StringIO()
                with redirect_stdout(output):
                    ui.show_disk_summary(before, cleaner.Stats(bytes=gib), False, after)
                text = output.getvalue()
                self.assertIn("BEFORE", text)
                self.assertIn("File data removed", text)
                self.assertIn(label, text)
                self.assertIn(expected + " (measured)", text)
                self.assertNotIn("AFTER (EST.)", text)

    def test_disk_summary_handles_missing_or_zero_capacity(self):
        for before in (None, cleaner.DiskSpace(0, 0, 0)):
            with self.subTest(before=before):
                output = io.StringIO()
                with redirect_stdout(output):
                    cleaner.Display().show_disk_summary(before, cleaner.Stats(), True)
                self.assertIn("unavailable" if before is None else "0.0%", output.getvalue())

    def test_main_captures_disk_usage_before_displaying_final_results(self):
        gib = 1024 ** 3
        for mode, expected in (("--dry-run", ["execute", "disk", "summary"]), ("--yes", ["disk", "execute", "disk", "summary"])):
            with self.subTest(mode=mode):
                self.put("app/bin/console")
                self.put("app/var/log/dev.log")
                order = []
                ui = cleaner.Display()
                ui.tty = False
                original_execute = cleaner.execute_plan

                def execute(*args, **kwargs):
                    order.append("execute")
                    return original_execute(*args, **kwargs)

                def disk(root):
                    self.assertEqual(root, self.root)
                    order.append("disk")
                    return cleaner.DiskSpace(1024 * gib, 768 * gib, 256 * gib)

                with redirect_stdout(io.StringIO()), mock.patch.object(cleaner.sys, "argv", [str(SCRIPT), "--kind", "logs", mode]), mock.patch.object(cleaner.Path, "home", return_value=self.base), mock.patch.object(cleaner, "Display", return_value=ui), mock.patch.object(ui, "open_log"), mock.patch.object(ui, "show_summary", side_effect=lambda: order.append("summary")), mock.patch.object(cleaner, "execute_plan", side_effect=execute), mock.patch.object(cleaner, "read_disk_usage", side_effect=disk):
                    status = cleaner.main()
                self.assertEqual(status, 0)
                self.assertEqual(order, expected)

    def test_preview_summarizes_directories_and_keeps_file_details_in_report(self):
        self.put("app/bin/console")
        examples = (("empty", "", "0 B"), ("small", "hello", "5 B"), ("long-" + "x" * 100, "x" * 2048, "2.0 KiB"))
        files = {}
        for kind, directory, extension in (("logs", "var/log", ".log"), ("cache", "var/cache/dev", ".php")):
            files[kind] = [(self.put("app/{}/{}{}".format(directory, name, extension), content), size) for name, content, size in examples]
        for kind in ("logs", "cache"):
            plan = cleaner.build_plan(self.root, self.events.append, kind=kind)
            for color in (True, False):
                with self.subTest(kind=kind, color=color):
                    output = io.StringIO()
                    ui = cleaner.Display()
                    ui.color = color
                    ui.tty = False
                    ui.log = io.StringIO()
                    with redirect_stdout(output):
                        stats = cleaner.execute_plan(plan, True, ui)
                        ui.show_summary()
                        report = ui.log.getvalue()
                        ui.close()
                    self.assertIn("app/var/log" if kind == "logs" else "app/var/cache", output.getvalue())
                    self.assertIn("2.0 KiB", output.getvalue())
                    for path, size in files[kind]:
                        relative = path.relative_to(self.root).as_posix()
                        self.assertNotIn(path.name, output.getvalue())
                        self.assertIn(relative + "  (" + size + ")", report)
                    self.assertNotIn("WOULD REMOVE", output.getvalue())
                    self.assertNotIn("\r", output.getvalue())
                    self.assertEqual(stats.files, len(examples))
                    self.assertEqual(stats.errors, 0)
                    self.assertTrue(all(path.exists() for group in files.values() for path, _ in group))

    def test_loose_logs_are_grouped_by_directory(self):
        self.put("app/bin/console")
        self.put("app/one.log", "123")
        self.put("app/two.log", "1234")
        self.put("app/nested/three.log", "12345")
        plan = cleaner.build_plan(self.root, self.events.append, kind="logs")
        output = io.StringIO()
        ui = cleaner.Display()
        ui.tty = False
        with redirect_stdout(output):
            cleaner.execute_plan(plan, True, ui)
            ui.show_summary()
        self.assertRegex(output.getvalue(), r"(?m)^\s*2\s+7 B\s+app$")
        self.assertRegex(output.getvalue(), r"(?m)^\s*1\s+5 B\s+app/nested$")
        self.assertNotIn("one.log", output.getvalue())

    def make_large_summary(self):
        self.put("app/bin/console")
        for number in range(30):
            self.put("app/extra-{:02d}/debug.log".format(number), "x" * (number + 1))
        plan = cleaner.build_plan(self.root, self.events.append, kind="logs")
        ui = cleaner.Display()
        ui.tty = False
        ui.log = io.StringIO()
        with redirect_stdout(io.StringIO()):
            cleaner.execute_plan(plan, True, ui)
        return ui

    def test_noninteractive_summary_is_bounded_and_report_has_all_directories(self):
        ui = self.make_large_summary()
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(cleaner.shutil, "get_terminal_size", return_value=os.terminal_size((80, 24))):
            ui.show_summary()
        self.assertLessEqual(len(output.getvalue().splitlines()), 16)
        self.assertIn("smaller directories included in totals", output.getvalue())
        self.assertIn("app/extra-29", output.getvalue())
        for number in range(30):
            self.assertIn("app/extra-{:02d}".format(number), ui.log.getvalue())
        ui.close()

    def test_long_interactive_summary_never_opens_viewer_or_requests_input(self):
        ui = self.make_large_summary()
        ui.tty = True
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(cleaner.sys.stdin, "isatty", return_value=True), mock.patch.object(cleaner.shutil, "get_terminal_size", return_value=os.terminal_size((80, 24))), mock.patch.object(subprocess, "run", side_effect=AssertionError("Never open an external viewer")), mock.patch("builtins.input", side_effect=AssertionError("Never request a key to close results")):
            ui.show_summary()
        self.assertIn("smaller directories included in totals", output.getvalue())
        self.assertIn("app/extra-29", output.getvalue())
        self.assertNotIn("q to return", output.getvalue())
        self.assertLessEqual(len(output.getvalue().splitlines()), 16)
        ui.close()

    def test_yes_mode_finishes_without_opening_external_viewer(self):
        self.make_large_summary().close()
        ui = cleaner.Display()
        ui.tty = True
        ui.color = False
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(cleaner.sys, "argv", [str(SCRIPT), "--kind", "logs", "--yes"]), mock.patch.object(cleaner.Path, "home", return_value=self.base), mock.patch.object(cleaner, "Display", return_value=ui), mock.patch.object(ui, "open_log"), mock.patch.object(cleaner.sys.stdin, "isatty", return_value=True), mock.patch.object(cleaner.shutil, "get_terminal_size", return_value=os.terminal_size((80, 24))), mock.patch.object(subprocess, "run") as viewer:
            status = cleaner.main()
        self.assertEqual(status, 0)
        viewer.assert_not_called()
        self.assertIn("CLEANUP COMPLETE", output.getvalue())
        self.assertFalse(any(self.root.rglob("*.log")))

    def test_interactive_completion_shows_savings_before_close_action(self):
        gib = 1024 ** 3
        before = cleaner.DiskSpace(1024 * gib, 768 * gib, 256 * gib)
        after = cleaner.DiskSpace(1024 * gib, 752 * gib, 272 * gib)
        for kind in ("logs", "cache"):
            for choice in ("2", "1"):
                with self.subTest(kind=kind, choice=choice):
                    self.put("app/bin/console")
                    for number in range(30):
                        suffix = "debug.log" if kind == "logs" else ".cache/item"
                        self.put("app/extra-{:02d}/{}".format(number, suffix))
                    ui = cleaner.Display()
                    ui.tty = True
                    ui.color = False
                    output = io.StringIO()
                    snapshots = [before] if choice == "2" else [before, after]
                    prompts = []

                    def respond(prompt):
                        prompts.append(prompt)
                        if len(prompts) == 1:
                            return choice
                        self.assertIn("Press Enter to close", prompt)
                        self.assertIn("DISK SPACE", output.getvalue())
                        self.assertIn("Estimated savings" if choice == "2" else "Space saved", output.getvalue())
                        return ""

                    with redirect_stdout(output), mock.patch.object(output, "isatty", return_value=True), mock.patch.object(cleaner.sys.stdin, "isatty", return_value=True), mock.patch.object(cleaner.sys, "argv", [str(SCRIPT), "--kind", kind]), mock.patch.object(cleaner.Path, "home", return_value=self.base), mock.patch.object(cleaner, "Display", return_value=ui), mock.patch.object(ui, "open_log"), mock.patch.object(cleaner, "read_disk_usage", side_effect=snapshots), mock.patch("builtins.input", side_effect=respond) as prompt, mock.patch.object(subprocess, "run", side_effect=AssertionError("Never open an external viewer")):
                        status = cleaner.main()
                    self.assertEqual(status, 0)
                    self.assertEqual(prompt.call_count, 2)
                    text = output.getvalue()
                    self.assertIn("PREVIEW COMPLETE" if choice == "2" else "CLEANUP COMPLETE", text)
                    self.assertIn("DISK SPACE", text)
                    self.assertIn("AFTER", text)
                    self.assertIn("256.0 GiB", text)
                    self.assertIn("Estimated savings" if choice == "2" else "Space saved", text)
                    if choice == "1":
                        self.assertIn("272.0 GiB", text)
                        self.assertIn("+16.0 GiB (measured)", text)
                    self.assertNotIn("Press Return", text)
                    self.assertNotIn("q to return", text)
                    self.assertNotIn("Full report:", text)

    def test_terminal_lifetime_keeps_summary_visible_until_enter(self):
        code = (
            "import io, runpy, sys\n"
            "from pathlib import Path\n"
            "from unittest import mock\n"
            "module = runpy.run_path(sys.argv[1], run_name='terminal_lifetime')\n"
            "root = Path(sys.argv[2])\n"
            "sys.argv = [sys.argv[1], '--kind', sys.argv[3]]\n"
            "with mock.patch.object(module['Path'], 'home', return_value=root), mock.patch.object(module['Display'], 'open_log', lambda self, path: setattr(self, 'log', io.StringIO())):\n"
            "    raise SystemExit(module['main']())\n"
        )
        for kind in ("logs", "cache"):
            for choice in ("2", "1"):
                with self.subTest(kind=kind, choice=choice):
                    self.put("app/bin/console")
                    self.put("app/var/log/dev.log" if kind == "logs" else "app/var/cache/dev/item.php")
                    master, slave = pty.openpty()
                    child_env = dict(os.environ, TERM="xterm-256color", COLUMNS="80", LINES="24")
                    child_env.pop("NO_COLOR", None)
                    process = subprocess.Popen([sys.executable, "-B", "-c", code, str(SCRIPT), str(self.base), kind], stdin=slave, stdout=slave, stderr=slave, env=child_env)
                    os.close(slave)
                    output = b""
                    answered = False
                    deadline = time.monotonic() + 8
                    try:
                        while time.monotonic() < deadline:
                            if select.select([master], [], [], 0.1)[0]:
                                try:
                                    chunk = os.read(master, 65536)
                                except OSError:
                                    break
                                if not chunk:
                                    break
                                output += chunk
                            if b"Select [1]:" in output and not answered:
                                os.write(master, choice.encode() + b"\n")
                                answered = True
                            if b"Press Enter to close this window" in output or process.poll() is not None:
                                break
                        screen = b"\n".join(output.split(b"\n")[-24:])
                        self.assertIn(b"DISK SPACE", screen, output.decode(errors="replace"))
                        self.assertIn(b"Estimated savings" if choice == "2" else b"Space saved", screen)
                        self.assertIn(b"AFTER", screen)
                        self.assertIn(b"Press Enter to close this window", screen)
                        with self.assertRaises(subprocess.TimeoutExpired):
                            process.wait(timeout=0.2)
                        os.write(master, b"\n")
                        self.assertEqual(process.wait(timeout=2), 0)
                    finally:
                        os.close(master)
                        if process.poll() is None:
                            process.kill()
                            process.wait()

    def test_cleanup_progress_updates_one_line_even_without_color(self):
        self.put("app/bin/console")
        for number in range(12):
            self.put("app/var/log/{:02d}.log".format(number))
        plan = cleaner.build_plan(self.root, self.events.append, kind="logs")
        ui = cleaner.Display()
        ui.tty = True
        ui.color = False
        ui.log = io.StringIO()
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(cleaner.time, "monotonic", side_effect=range(100)):
            stats = cleaner.execute_plan(plan, False, ui)
            ui.clear_progress()
        self.assertEqual(stats.files, 12)
        self.assertIn("Removed", output.getvalue())
        self.assertIn("11.log", output.getvalue())
        self.assertIn("\r", output.getvalue())
        self.assertEqual(output.getvalue().count("\n"), 0)
        self.assertIn("app/var/log/00.log", ui.log.getvalue())
        self.assertIn("app/var/log/11.log", ui.log.getvalue())
        ui.close()

    def test_repeated_errors_do_not_flood_terminal(self):
        ui = cleaner.Display()
        ui.tty = False
        ui.log = io.StringIO()
        output = io.StringIO()
        with redirect_stdout(output):
            for number in range(50):
                ui({"level": "ERROR", "message": "file-{}: permission denied".format(number)})
        self.assertLessEqual(len(output.getvalue().splitlines()), 3)
        self.assertIn("file-49", ui.log.getvalue())
        ui.close()

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
                            os.write(master, b"q\n")
                            answered = True
                        if process.poll() is not None:
                            break
                    self.assertEqual(process.wait(timeout=1), 0)
                    self.assertIn(title.encode(), output)
                    self.assertIn(action.encode(), output)
                    self.assertIn(b"\x1b[", output)
                    self.assertNotIn(b"Scanning apps", output)
                    self.assertNotIn(b"Press Return", output)
                finally:
                    os.close(master)
                    if process.poll() is None:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    unittest.main(verbosity=2)
