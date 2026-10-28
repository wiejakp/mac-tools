"""Network mount tests: mocked servers only; never inspect a mounted share."""
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

REPO_ROOT = Path(__file__).absolute().parents[1]
SCRIPT = REPO_ROOT / "src/local_scripts/network_mounts.py"
loader = importlib.machinery.SourceFileLoader("network_mounts", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
mounts = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = mounts
loader.exec_module(mounts)

WORK = "smb://cch-fp01/users%24/Home/pwiejak"
HOME = ("smb://192.168.2.118/pwiam/SSD1", "smb://192.168.2.118/pwiam/SSD2")


class NetworkMountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".mounts-test-", dir=REPO_ROOT / "tests")
        self.root = Path(self.temp.name)
        self.profiles = {
            "work": mounts.Profile("work", "Work VPN", (WORK,)),
            "home": mounts.Profile("home", "Home NAS", HOME),
        }

    def tearDown(self):
        self.temp.cleanup()

    def config(self, data=None):
        directory = self.root / "config"
        directory.mkdir(exist_ok=True)
        path = directory / "mounts.local.json"
        path.write_text(json.dumps(data or {
            "work": {"label": "Work VPN", "urls": [WORK]},
            "home": {"label": "Home NAS", "server": "192.168.2.118", "discover_shares": True},
        }))
        return path

    def test_profiles_preserve_work_subfolder_and_discover_home_without_drive_list(self):
        self.config()
        profiles = mounts.load_profiles(self.root)
        self.assertEqual(profiles["work"].urls, (WORK,))
        self.assertEqual(profiles["home"].urls, ())
        self.assertEqual(profiles["home"].host, "192.168.2.118")
        self.assertTrue(profiles["home"].discover_shares)

    def discovered_home(self):
        self.profiles["home"] = mounts.Profile("home", "Home NAS", server="192.168.2.118", discover_shares=True)
        return self.profiles["home"]

    def test_share_catalogue_keeps_disk_shares_and_does_not_assume_ssd_names(self):
        output = "Share                           Type    Comments\n------------------------------- ------- --------\nMedia                           Disk    Shared media\nBackup Archive                  Disk    Backups\nSSD17                           Disk\nIPC$                            Pipe    IPC service\nprint$                          Printer Printer drivers\nMedia                           Disk\n"
        self.assertEqual(mounts.parse_share_catalogue(output), ("Backup Archive", "Media", "SSD17"))

    def test_authenticated_discovery_passes_no_password_in_arguments(self):
        secret = "dummy-private-password"
        output = "Share                           Type    Comments\nMedia                           Disk\nBackup Archive                  Disk\n"
        with mock.patch.object(mounts, "_run_password_command", return_value=(0, output)) as native:
            urls = mounts.discover_shares("192.168.2.118", "DOMAIN\\home-user", secret, 10)
        self.assertEqual(urls, ("smb://192.168.2.118/Backup%20Archive", "smb://192.168.2.118/Media"))
        command, password, timeout = native.call_args.args
        self.assertEqual(command[:3], ["/usr/bin/smbutil", "view", "-f"])
        self.assertNotIn(secret, " ".join(command))
        self.assertEqual(password, secret)
        self.assertEqual(timeout, 10)

    def test_discovered_drives_can_all_be_mounted_with_one_choice_and_login(self):
        self.discovered_home()
        drives = tuple("smb://192.168.2.118/Volume{}".format(number) for number in range(1, 10))
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["home-user", "all"]) as prompt, mock.patch.object(mounts.getpass, "getpass", return_value="home-secret") as password, mock.patch.object(mounts, "discover_shares", return_value=drives) as discover, mock.patch.object(mounts, "mount_volume") as mount, mock.patch.object(mounts.os, "listdir", side_effect=AssertionError("No directory browsing")), mock.patch.object(mounts.os, "scandir", side_effect=AssertionError("No directory browsing")):
            results = mounts.run_profiles(self.profiles, ("home",))
        self.assertEqual([call.args[0] for call in mount.call_args_list], list(drives))
        self.assertTrue(all(call.args[1:3] == ("home-user", "home-secret") for call in mount.call_args_list))
        self.assertEqual(prompt.call_count, 2)
        password.assert_called_once()
        discover.assert_called_once_with("192.168.2.118", "home-user", "home-secret", 35)
        self.assertTrue(all(result.status == "Mounted" for result in results))

    def test_all_option_skips_selection_prompt_and_keeps_work_credentials_separate(self):
        self.discovered_home()
        drives = ("smb://192.168.2.118/Media", "smb://192.168.2.118/Backup")
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["work-user", "home-user"]) as prompt, mock.patch.object(mounts.getpass, "getpass", side_effect=["work-secret", "home-secret"]), mock.patch.object(mounts, "discover_shares", return_value=drives) as discover, mock.patch.object(mounts, "mount_volume") as mount:
            mounts.run_profiles(self.profiles, ("work", "home"), mount_all=True)
        self.assertEqual(prompt.call_count, 2)
        discover.assert_called_once_with("192.168.2.118", "home-user", "home-secret", 35)
        self.assertEqual([call.args[:3] for call in mount.call_args_list], [(WORK, "work-user", "work-secret"), (drives[0], "home-user", "home-secret"), (drives[1], "home-user", "home-secret")])

    def test_discovered_drive_selection_supports_individual_drives_and_ranges(self):
        drives = tuple("smb://192.168.2.118/Data{}".format(n) for n in range(1, 6))
        with redirect_stdout(io.StringIO()), mock.patch("builtins.input", return_value="1,3-4"):
            self.assertEqual(mounts.choose_discovered_urls(drives), (drives[0], drives[2], drives[3]))
        with redirect_stdout(io.StringIO()), mock.patch("builtins.input", return_value=""):
            self.assertEqual(mounts.choose_discovered_urls(drives), drives)
        with redirect_stdout(io.StringIO()), mock.patch("builtins.input", return_value="0"):
            self.assertEqual(mounts.choose_discovered_urls(drives), ())

    def test_discovery_failure_does_not_reveal_error_payload_or_block_other_profile(self):
        self.discovered_home()
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["home-user", "work-user"]), mock.patch.object(mounts.getpass, "getpass", side_effect=["home-secret", "work-secret"]), mock.patch.object(mounts, "discover_shares", side_effect=mounts.MountError("Share discovery failed.")), mock.patch.object(mounts, "mount_volume") as mount:
            results = mounts.run_profiles(self.profiles, ("home", "work"))
        mount.assert_called_once_with(WORK, "work-user", "work-secret", 35)
        self.assertEqual([result.status for result in results], ["Failed", "Mounted"])

    def test_discovery_preview_never_requests_catalogue_or_credentials(self):
        self.discovered_home()
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "discover_shares") as discover, mock.patch.object(mounts, "server_reachable") as probe, mock.patch("builtins.input") as username, mock.patch.object(mounts.getpass, "getpass") as password:
            results = mounts.run_profiles(self.profiles, ("home",), dry_run=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "Preview")
        for operation in (discover, probe, username, password):
            operation.assert_not_called()

    def test_private_command_uses_a_real_hidden_password_prompt_without_network(self):
        secret = 'dummy-secret-"\\!'
        code = "import getpass; p=getpass.getpass('Password: '); print(p); print('\\nShare                           Type    Comments\\nMedia                           Disk')"
        status, output = mounts._run_password_command([sys.executable, "-B", "-c", code], secret, 3)
        self.assertEqual(status, 0)
        self.assertIn("Media", output)
        self.assertNotIn(secret, output)

    def test_private_command_timeout_is_bounded_and_sanitized(self):
        with self.assertRaises(mounts.MountError) as error:
            mounts._run_password_command([sys.executable, "-B", "-c", "import time; time.sleep(5)"], "private-test-password", 0.1)
        self.assertIn("timed out", str(error.exception))
        self.assertNotIn("private-test-password", str(error.exception))

    def test_configuration_rejects_credentials_and_symlinks(self):
        self.config({"work": {"urls": [WORK], "password": "do-not-leak"}, "home": {"urls": list(HOME)}})
        with self.assertRaises(mounts.ConfigError) as error:
            mounts.load_profiles(self.root)
        self.assertNotIn("do-not-leak", str(error.exception))
        path = self.root / "config/mounts.local.json"
        path.unlink()
        other = self.root / "elsewhere.json"
        other.write_text("{}")
        path.symlink_to(other)
        with self.assertRaises(mounts.ConfigError):
            mounts.load_profiles(self.root)

    def test_urls_must_be_specific_smb_paths_without_embedded_credentials(self):
        for value in ("smb://server/", "https://server/share", "smb://user:secret@server/share", "smb://server/share/../private", "smb://server/share?password=secret"):
            with self.subTest(url=value), self.assertRaises(mounts.ConfigError):
                mounts.validate_url(value)

    def test_unconfirmed_work_can_be_skipped_without_blocking_home(self):
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", side_effect=lambda host, timeout: host == "192.168.2.118"), mock.patch("builtins.input", side_effect=["", "home-user"]) as username, mock.patch.object(mounts.getpass, "getpass", return_value="home-secret") as password, mock.patch.object(mounts, "mount_volume") as mount:
            results = mounts.run_profiles(self.profiles, ("work", "home"))
        self.assertEqual([call.args[0] for call in mount.call_args_list], list(HOME))
        self.assertTrue(all(call.args[1:3] == ("home-user", "home-secret") for call in mount.call_args_list))
        self.assertEqual(username.call_count, 2)
        self.assertEqual(password.call_count, 1)
        self.assertEqual([result.status for result in results], ["Skipped", "Mounted", "Mounted"])

    def test_failed_quick_probe_does_not_prevent_cch_native_mount(self):
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(mounts, "server_reachable", return_value=False), mock.patch("builtins.input", return_value="DOMAIN\\work-user"), mock.patch.object(mounts.getpass, "getpass", return_value="work-secret"), mock.patch.object(mounts, "mount_volume") as mount:
            results = mounts.run_profiles(self.profiles, ("work",))
        mount.assert_called_once_with(WORK, "DOMAIN\\work-user", "work-secret", 35)
        self.assertEqual([result.status for result in results], ["Mounted"])
        self.assertNotIn("connect the work VPN", output.getvalue())

    def test_cch_server_override_preserves_work_share_and_subfolder(self):
        profiles = mounts.with_cch_server(self.profiles, "files.cch.example")
        self.assertEqual(profiles["work"].urls, ("smb://files.cch.example/users%24/Home/pwiejak",))
        self.assertIs(profiles["home"], self.profiles["home"])
        self.assertEqual(self.profiles["work"].urls, (WORK,))
        for address in ("smb://server/share", "user:secret@server", "server/share", "server?password=secret"):
            with self.subTest(address=address), self.assertRaises(mounts.ConfigError) as error:
                mounts.with_cch_server(self.profiles, address)
            self.assertNotIn("secret", str(error.exception))

    def test_cch_server_override_is_available_from_the_named_launcher(self):
        config = self.config()
        result = subprocess.run([str(REPO_ROOT / "mount-cch.sh"), "--dry-run", "--config", str(config), "--cch-server", "10.20.30.40"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("smb://10.20.30.40/users%24/Home/pwiejak", result.stdout)
        self.assertNotIn("192.168.2.118", result.stdout)

    def test_credentials_are_separate_and_mounts_run_sequentially(self):
        seen = []

        def mount(url, username, password, timeout):
            seen.append((url, username, password))

        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["work-user", "home-user"]), mock.patch.object(mounts.getpass, "getpass", side_effect=["work-secret", "home-secret"]), mock.patch.object(mounts, "mount_volume", side_effect=mount):
            mounts.run_profiles(self.profiles, ("work", "home"))
        self.assertEqual(seen, [(WORK, "work-user", "work-secret"), (HOME[0], "home-user", "home-secret"), (HOME[1], "home-user", "home-secret")])

    def test_one_failed_mount_does_not_stop_other_mounts(self):
        def mount(url, *args):
            if url == WORK:
                raise mounts.MountError("Mount failed; check network, path and credentials.")

        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["work-user", "home-user"]), mock.patch.object(mounts.getpass, "getpass", side_effect=["work-secret", "home-secret"]), mock.patch.object(mounts, "mount_volume", side_effect=mount):
            results = mounts.run_profiles(self.profiles, ("work", "home"))
        self.assertEqual([r.status for r in results], ["Failed", "Mounted", "Mounted"])
        self.assertNotIn("work-secret", output.getvalue())
        self.assertNotIn("home-secret", output.getvalue())

    def test_home_paths_can_be_corrected_without_listing_share_contents(self):
        self.profiles["home"] = mounts.Profile("home", "Home NAS", HOME, True)
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch("builtins.input", side_effect=["pwiam/ssd2, SSD3", "home-user"]), mock.patch.object(mounts.getpass, "getpass", return_value="home-secret"), mock.patch.object(mounts, "mount_volume") as mount, mock.patch.object(mounts.os, "listdir", side_effect=AssertionError("Do not inspect network contents")), mock.patch.object(mounts.os, "scandir", side_effect=AssertionError("Do not inspect network contents")):
            mounts.run_profiles(self.profiles, ("home",))
        self.assertEqual([call.args[0] for call in mount.call_args_list], ["smb://192.168.2.118/pwiam/ssd2", "smb://192.168.2.118/SSD3"])

    def test_preview_does_not_connect_mount_or_request_credentials(self):
        with redirect_stdout(io.StringIO()), mock.patch.object(mounts, "server_reachable") as probe, mock.patch.object(mounts, "mount_volume") as mount, mock.patch("builtins.input") as username, mock.patch.object(mounts.getpass, "getpass") as password:
            results = mounts.run_profiles(self.profiles, ("work", "home"), dry_run=True)
        self.assertEqual([r.status for r in results], ["Preview", "Preview", "Preview"])
        for operation in (probe, mount, username, password):
            operation.assert_not_called()

    def test_native_mount_keeps_password_out_of_arguments_and_error_messages(self):
        secret = 'private-p@ss:"\\word'
        response = subprocess.CompletedProcess([], 0, "OK\n", "")
        with mock.patch.object(mounts.subprocess, "run", return_value=response) as native:
            mounts.mount_volume(WORK, "DOMAIN\\user", secret, 30)
        self.assertEqual(native.call_args.args[0], ["/usr/bin/osascript", "-"])
        self.assertTrue(all(secret not in arg for arg in native.call_args.args[0]))
        self.assertNotIn("shell", native.call_args.kwargs)
        self.assertIn(WORK, native.call_args.kwargs["input"])
        response = subprocess.CompletedProcess([], 1, "ERROR:-36\n", "echo " + secret)
        with mock.patch.object(mounts.subprocess, "run", return_value=response), self.assertRaises(mounts.MountError) as error:
            mounts.mount_volume(WORK, "DOMAIN\\user", secret, 30)
        self.assertNotIn(secret, str(error.exception))

    def test_native_mount_source_compiles_without_running_it(self):
        script = mounts.mount_script(WORK, 'DOMAIN\\user"name', 'test-only-"\\$é-password', 30)
        result = subprocess.run(["/usr/bin/osacompile", "-o", str(self.root / "mount.scpt"), "-"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reachability_uses_only_smb_port_and_handles_failures(self):
        with mock.patch.object(mounts.socket, "create_connection") as connection:
            self.assertTrue(mounts.server_reachable("192.168.2.118", 1))
        connection.assert_called_once_with(("192.168.2.118", 445), timeout=1)
        with mock.patch.object(mounts.socket, "create_connection", side_effect=OSError("not on this network")):
            self.assertFalse(mounts.server_reachable("cch-fp01", 1))

    def test_slow_name_resolution_cannot_block_other_profiles(self):
        release = threading.Event()

        def stalled(*args, **kwargs):
            release.wait(1)
            raise OSError("offline")

        try:
            with mock.patch.object(mounts.socket, "create_connection", side_effect=stalled):
                started = time.monotonic()
                self.assertFalse(mounts.server_reachable("server-not-resolving", 0.02))
                self.assertLess(time.monotonic() - started, 0.6)
        finally:
            release.set()

    def test_native_timeouts_have_a_safe_message(self):
        secret = "test-only-private-password"
        with mock.patch.object(mounts.subprocess, "run", side_effect=subprocess.TimeoutExpired(["osascript"], 1)), self.assertRaises(mounts.MountError) as error:
            mounts.mount_volume(WORK, "user", secret, 1)
        self.assertIn("timed out", str(error.exception))
        self.assertNotIn(secret, str(error.exception))

    def test_shell_entry_points_preview_only_their_own_profiles(self):
        config = self.config()
        entries = (
            ("mount.sh", ("cch-fp01", "192.168.2.118")),
            ("mount-home.sh", ("192.168.2.118",)),
            ("mount-cch.sh", ("cch-fp01",)),
            ("launchers/Mount All.command", ("cch-fp01", "192.168.2.118")),
            ("launchers/Mount Home.command", ("192.168.2.118",)),
            ("launchers/Mount CCH.command", ("cch-fp01",)),
        )
        for name, hosts in entries:
            with self.subTest(script=name):
                entry = REPO_ROOT / name
                self.assertTrue(os.access(entry, os.X_OK))
                result = subprocess.run([str(entry), "--dry-run", "--config", str(config)], cwd=REPO_ROOT / "tests", capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for host in hosts:
                    self.assertIn(host, result.stdout)
                for host in {"cch-fp01", "192.168.2.118"} - set(hosts):
                    self.assertNotIn(host, result.stdout)
                result = subprocess.run([str(entry), "--help"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)

    def test_complete_summary_is_visible_before_enter_to_close(self):
        output = io.StringIO()
        values = iter(["work-user", "home-user"])

        def answer(prompt):
            if "Press Enter to close" in prompt:
                self.assertIn("MOUNT SUMMARY", output.getvalue())
                self.assertIn("Mounted", output.getvalue())
                return ""
            return next(values)

        with redirect_stdout(output), mock.patch.object(output, "isatty", return_value=True), mock.patch.object(mounts.sys.stdin, "isatty", return_value=True), mock.patch.object(mounts.sys, "argv", [str(SCRIPT), "--profile", "all"]), mock.patch.object(mounts, "load_profiles", return_value=self.profiles), mock.patch.object(mounts, "server_reachable", return_value=True), mock.patch.object(mounts, "mount_volume"), mock.patch("builtins.input", side_effect=answer), mock.patch.object(mounts.getpass, "getpass", side_effect=["work-secret", "home-secret"]):
            status = mounts.main()
        self.assertEqual(status, 0)
        self.assertNotIn("work-secret", output.getvalue())
        self.assertNotIn("home-secret", output.getvalue())

    def test_terminal_passwords_are_hidden_and_summary_waits_for_enter(self):
        code = (
            "import runpy, sys\n"
            "from unittest import mock\n"
            "m = runpy.run_path(sys.argv[1], run_name='mount_terminal_test')\n"
            "profiles = {'work': m['Profile']('work', 'Work VPN', (" + repr(WORK) + ",)), 'home': m['Profile']('home', 'Home NAS', server='192.168.2.118', discover_shares=True)}\n"
            "sys.argv = [sys.argv[1], '--profile', 'all']\n"
            "with mock.patch.dict(m['main'].__globals__, {'load_profiles': lambda *args: profiles, 'server_reachable': lambda *args: True, 'discover_shares': lambda *args: " + repr(HOME) + ", 'mount_volume': lambda *args: None}):\n"
            "    raise SystemExit(m['main']())\n"
        )
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(SCRIPT)], stdin=slave, stdout=slave, stderr=slave, start_new_session=True, env=dict(os.environ, TERM="xterm-256color"))
        os.close(slave)
        dialogue = [
            (b"Work VPN username:", b"work-user\n"),
            (b"Work VPN password (hidden):", b"never-echo-work\n"),
            (b"Home NAS username:", b"home-user\n"),
            (b"Home NAS password (hidden):", b"never-echo-home\n"),
            (b"Mount [all],", b"all\n"),
        ]
        output = b""
        step = 0
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
                if step < len(dialogue) and dialogue[step][0] in output:
                    os.write(master, dialogue[step][1])
                    step += 1
                if b"Press Enter to close this window" in output or process.poll() is not None:
                    break
            self.assertEqual(step, len(dialogue), output.decode(errors="replace"))
            self.assertNotIn(b"never-echo-work", output)
            self.assertNotIn(b"never-echo-home", output)
            self.assertIn(b"MOUNT SUMMARY", output)
            self.assertIn(b"3 mounted", output)
            self.assertIn(b"Press Enter to close this window", output)
            with self.assertRaises(subprocess.TimeoutExpired):
                process.wait(timeout=0.2)
            os.write(master, b"\n")
            self.assertEqual(process.wait(timeout=2), 0)
        finally:
            os.close(master)
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    unittest.main(verbosity=2)
