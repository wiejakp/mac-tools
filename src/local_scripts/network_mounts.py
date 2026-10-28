#!/usr/bin/python3
"""Mount configured SMB URLs sequentially, without browsing share contents."""
import argparse
from dataclasses import dataclass, replace
import getpass
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import socket
import subprocess
import sys
import termios
import threading
import time
from urllib.parse import quote, unquote, urlsplit, urlunsplit


class ConfigError(Exception):
    pass


class MountError(Exception):
    pass


@dataclass(frozen=True)
class Profile:
    name: str
    label: str
    urls: tuple = ()
    confirm_paths: bool = False
    server: str = ""
    discover_shares: bool = False

    @property
    def host(self):
        return self.server or urlsplit(self.urls[0]).hostname


@dataclass(frozen=True)
class MountResult:
    profile: str
    url: str
    status: str
    detail: str = ""


def safe(value):
    return "".join(char if char.isprintable() else "?" for char in str(value))


def say(level, message):
    colors = {"CHECK": "36", "MOUNT": "36", "Mounted": "32", "Failed": "31", "Skipped": "33", "ERROR": "31"}
    label = "{:<9}".format(level)
    if sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb":
        label = "\033[{}m{}\033[0m".format(colors.get(level, "37"), label)
    print("  {} {}".format(label, safe(message)), flush=True)


def validate_url(value):
    try:
        if not isinstance(value, str) or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError()
        parts = urlsplit(value)
        if parts.scheme != "smb" or not parts.hostname or parts.username is not None or parts.password is not None:
            raise ValueError()
        if parts.port not in (None, 445) or parts.query or parts.fragment:
            raise ValueError()
        path = unquote(parts.path)
        if not path.strip("/") or "\\" in path or any(part in (".", "..") for part in path.split("/")):
            raise ValueError()
        if any(ord(char) < 32 or ord(char) == 127 for char in path):
            raise ValueError()
    except (ValueError, TypeError):
        raise ConfigError("Use a specific smb://server/share[/subfolder] URL without embedded credentials.") from None
    return value


def load_profiles(repo_root, config_path=None):
    root = Path(os.path.abspath(repo_root))
    path = Path(os.path.abspath(config_path)) if config_path is not None else root / "config/mounts.local.json"
    try:
        relative = path.relative_to(root)
        if not relative.parts:
            raise ValueError()
    except ValueError:
        raise ConfigError("The mount configuration must be inside this project.") from None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = None
    try:
        fd = os.open(root, flags)
        for part in relative.parts[:-1]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        source = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(source, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, ValueError):
        raise ConfigError("Cannot read the local mount configuration. Use a regular JSON file inside this project; config/mounts.example.json shows the format.") from None
    finally:
        if fd is not None:
            os.close(fd)
    if not isinstance(data, dict) or set(data) != {"home", "work"}:
        raise ConfigError("Configure separate home and work profiles.")
    profiles = {}
    for name in ("work", "home"):
        entry = data[name]
        if not isinstance(entry, dict) or set(entry) - {"label", "urls", "confirm_paths", "server", "discover_shares"}:
            raise ConfigError("Store mount paths or discovery settings only. Enter credentials at the prompts.")
        label = entry.get("label", name.title())
        confirm = entry.get("confirm_paths", False)
        discover = entry.get("discover_shares", False)
        if not isinstance(label, str) or not label.strip() or safe(label) != label or not isinstance(confirm, bool) or not isinstance(discover, bool):
            raise ConfigError("Use a printable profile label and boolean selection/discovery settings.")
        if discover:
            server = entry.get("server")
            if name != "home" or not isinstance(server, str) or not server or entry.get("urls") or confirm:
                raise ConfigError("For home discovery, configure a server without a fixed drive list.")
            try:
                if any(char.isspace() or char in "/\\@?#" for char in server):
                    raise ValueError()
                parsed = urlsplit("smb://" + server)
                if not parsed.hostname or parsed.port not in (None, 445):
                    raise ValueError()
            except ValueError:
                raise ConfigError("Use a plain home server hostname or IP address.") from None
            profiles[name] = Profile(name, label, server=parsed.hostname, discover_shares=True)
        else:
            urls = entry.get("urls")
            if not isinstance(urls, list) or not urls:
                raise ConfigError("Each fixed profile must contain at least one SMB URL.")
            urls = tuple(validate_url(url) for url in urls)
            if len({urlsplit(url).hostname.casefold() for url in urls}) != 1:
                raise ConfigError("Keep each server's credentials in a separate profile.")
            profiles[name] = Profile(name, label, tuple(dict.fromkeys(urls)), confirm)
    return profiles


def server_reachable(host, timeout):
    """Bound even slow DNS; make one SMB-port connection, without authentication."""
    reachable = threading.Event()

    def check():
        try:
            with socket.create_connection((host, 445), timeout=timeout):
                reachable.set()
        except OSError:
            pass

    worker = threading.Thread(target=check, daemon=True)
    worker.start()
    worker.join(timeout)
    return reachable.is_set()


def with_cch_server(profiles, server):
    """Use an explicitly supplied CCH hostname/IP without changing its path."""
    try:
        if not isinstance(server, str) or not server or any(char.isspace() or char in "/\\@?#" or ord(char) < 32 for char in server):
            raise ValueError()
        address = urlsplit("smb://" + server)
        if not address.hostname or address.port not in (None, 445):
            raise ValueError()
    except ValueError:
        raise ConfigError("Use a plain full CCH hostname or IP address, without a URL, path or credentials.") from None
    work = profiles["work"]
    urls = tuple(validate_url(urlunsplit((parts.scheme, server, parts.path, "", ""))) for parts in (urlsplit(url) for url in work.urls))
    updated = dict(profiles)
    updated["work"] = replace(work, urls=urls, server="")
    return updated


def apple_string(value):
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise MountError("The supplied values contain unsupported control characters.")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mount_script(url, username, password, timeout):
    # Literal strings go over stdin, never a shell command, argument or file.
    return (
        "try\n"
        "    with timeout of {timeout} seconds\n"
        "        mount volume {url} as user name {username} with password {password}\n"
        "    end timeout\n"
        '    return "OK"\n'
        "on error errorText number errorNumber\n"
        '    return "ERROR:" & (errorNumber as text)\n'
        "end try\n"
    ).format(timeout=max(1, int(timeout)), url=apple_string(validate_url(url)), username=apple_string(username), password=apple_string(password))


def mount_volume(url, username, password, timeout):
    script = mount_script(url, username, password, timeout)
    try:
        result = subprocess.run(["/usr/bin/osascript", "-"], input=script, text=True, capture_output=True, timeout=timeout + 2)
    except subprocess.TimeoutExpired:
        raise MountError("Connection timed out; other drives will still be attempted.") from None
    except OSError:
        raise MountError("The macOS mount service could not be started.") from None
    if result.returncode == 0 and result.stdout.strip() == "OK":
        return
    match = re.fullmatch(r"ERROR:(-?\d+)", result.stdout.strip())
    code = " (macOS {})".format(match.group(1)) if match else ""
    # Never echo native error payloads: they may include credential strings.
    raise MountError("Could not mount; check the share path, credentials and network" + code + ".")


def server_url(host):
    return "smb://" + ("[" + host + "]" if ":" in host else host) + "/"


def _run_password_command(command, password, timeout):
    """Feed one hidden password to a native client through a private terminal."""
    apple_string(password)  # Reject control characters, including injected newlines.
    environment = dict(os.environ, LC_ALL="C", LANG="C", TERM="dumb")
    try:
        pid, terminal = pty.fork()
    except OSError:
        raise MountError("Could not start private SMB share discovery.") from None
    if pid == 0:
        try:
            os.execve(command[0], command, environment)
        except OSError:
            os._exit(127)
    status = None
    output = b""
    sent = False
    last_prompt = -1
    eof = False
    deadline = time.monotonic() + timeout
    try:
        settings = termios.tcgetattr(terminal)
        settings[3] &= ~termios.ECHO
        termios.tcsetattr(terminal, termios.TCSANOW, settings)
        while time.monotonic() < deadline:
            readable = False
            if not eof:
                readable = bool(select.select([terminal], [], [], min(0.1, max(0, deadline - time.monotonic())))[0])
                if readable:
                    try:
                        chunk = os.read(terminal, 65536)
                    except OSError:
                        chunk = b""
                    if not chunk:
                        eof = True
                    else:
                        output += chunk
                        if len(output) > 2 * 1024 * 1024:
                            raise MountError("The server's share catalogue is too large to process safely.")
                        if not re.search(rb"(?im)^\s*Share\s+Type\b", output):
                            prompts = list(re.finditer(rb"(?im)(?:password|passphrase)[^\r\n]*:", output))
                            if prompts and prompts[-1].end() > last_prompt:
                                last_prompt = prompts[-1].end()
                                if sent:
                                    raise MountError("Share discovery authentication was rejected.")
                                os.write(terminal, (password + "\n").encode("utf-8"))
                                sent = True
            if status is None:
                done, value = os.waitpid(pid, os.WNOHANG)
                if done:
                    status = os.waitstatus_to_exitcode(value)
            if status is not None and (eof or not readable):
                text = output.decode("utf-8", errors="replace")
                return status, text.replace(password, "[redacted]") if password else text
            if eof:
                time.sleep(0.01)
        raise MountError("SMB share discovery timed out; other profiles will still be attempted.")
    except OSError:
        raise MountError("Could not read the SMB share catalogue; other profiles will still be attempted.") from None
    finally:
        os.close(terminal)
        if status is None:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


def parse_share_catalogue(output):
    """Read names/types from smbutil's catalogue, never a directory listing."""
    names = []
    for line in output.splitlines():
        row = re.match(r"^\s*(.*?)\s{2,}(Disk|Printer|Pipe)\b", line, re.IGNORECASE)
        if not row:
            row = re.match(r"^\s*(.*?)\t+(Disk|Printer|Pipe)\b", line, re.IGNORECASE)
        if not row or row.group(2).casefold() != "disk":
            continue
        name = row.group(1).strip()
        if not name or name in (".", "..") or any(char in "/\\" or ord(char) < 32 or ord(char) == 127 for char in name):
            continue
        names.append(name)
    return tuple(sorted(set(names), key=lambda name: [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", name)]))


def discover_shares(host, username, password, timeout):
    apple_string(username)
    if "\\" in username or ";" in username:
        domain, user = re.split(r"[\\;]", username, maxsplit=1)
        login = quote(domain, safe="") + ";" + quote(user, safe="")
    else:
        login = quote(username, safe="")
    authority = "[" + host + "]" if ":" in host else host
    command = ["/usr/bin/smbutil", "view", "-f", "//" + login + "@" + authority]
    status, output = _run_password_command(command, password, timeout)
    if status != 0:
        raise MountError("Could not discover home shares; check the username, password and network.")
    shares = parse_share_catalogue(output)
    if not shares:
        raise MountError("The server did not advertise any accessible disk shares. No folders were inspected.")
    return tuple(server_url(host) + quote(name, safe="") for name in shares)


def choose_discovered_urls(urls, mount_all=False):
    print("\n  HOME DRIVES · {} SMB shares discovered".format(len(urls)))
    for number, url in enumerate(urls, 1):
        print("  [{:>2}] {}".format(number, safe(unquote(urlsplit(url).path).lstrip("/"))))
    if mount_all:
        print("  Mounting all discovered drives.\n")
        return urls
    print("  [all] Mount all listed drives (default)")
    print("  [0]   Skip home drives\n")
    while True:
        answer = input("  Mount [all], numbers (1,3-5), or 0 to skip: ").strip().casefold()
        if answer in ("", "all", "a"):
            return urls
        if answer == "0":
            return ()
        try:
            numbers = set()
            for item in answer.split(","):
                if re.fullmatch(r"\d+", item.strip()):
                    numbers.add(int(item))
                elif re.fullmatch(r"\d+\s*-\s*\d+", item.strip()):
                    first, last = (int(value.strip()) for value in item.split("-"))
                    if not 1 <= first <= last <= len(urls):
                        raise ValueError()
                    numbers.update(range(first, last + 1))
                else:
                    raise ValueError()
            if not numbers or min(numbers) < 1 or max(numbers) > len(urls):
                raise ValueError()
            return tuple(url for number, url in enumerate(urls, 1) if number in numbers)
        except ValueError:
            print("  Choose all, 0, or valid numbers/ranges from the list.")


def choose_urls(profile):
    if not profile.confirm_paths:
        return profile.urls
    host = urlsplit(profile.urls[0]).hostname
    defaults = ", ".join(unquote(urlsplit(url).path).lstrip("/") for url in profile.urls)
    print("  Confirm the share paths; nothing inside the shares will be listed.")
    answer = input("  {} share paths [{}]: ".format(profile.label, defaults)).strip()
    if not answer:
        return profile.urls
    urls = []
    for value in answer.split(","):
        value = value.strip()
        if not value:
            continue
        url = value if value.startswith("smb://") else "smb://" + host + "/" + quote(value.strip("/"), safe="/%$")
        validate_url(url)
        if urlsplit(url).hostname.casefold() != host.casefold():
            raise ConfigError("Use share paths on the configured home server only.")
        urls.append(url)
    if not urls:
        raise ConfigError("Enter at least one share path.")
    return tuple(dict.fromkeys(urls))


def run_profiles(profiles, selected, dry_run=False, timeout=4, mount_timeout=35, mount_all=False):
    results = []
    for name in selected:
        profile = profiles[name]
        host = profile.host
        urls = profile.urls or (server_url(host),)
        if dry_run:
            for url in urls:
                detail = "Disk shares will be discovered after login; preview makes no connection." if profile.discover_shares else "Configured path; not validated or connected."
                results.append(MountResult(profile.label, url, "Preview", detail))
            continue
        say("CHECK", "{} — {}".format(profile.label, host))
        confirmed = server_reachable(host, timeout)
        if not confirmed and name != "work":
            reason = "SMB unavailable on this network; connect to your home network."
            say("Skipped", reason)
            results.extend(MountResult(profile.label, url, "Skipped", reason) for url in urls)
            continue
        if name == "work":
            if not confirmed:
                say("CHECK", "The quick CCH check could not confirm a connection. Enter credentials to try the native macOS SMB mount anyway.")
            print("  CCH login: DOMAIN\\username or username@domain. Leave the username blank to skip CCH.")
        try:
            if not profile.discover_shares:
                urls = choose_urls(profile)
            username = input("  {} username: ".format(profile.label)).strip()
            if not username and name == "work":
                results.extend(MountResult(profile.label, url, "Skipped", "CCH skipped by choice.") for url in urls)
                continue
            if not username:
                raise ConfigError("A username is required for this profile.")
            password = getpass.getpass("  {} password (hidden): ".format(profile.label))
            if profile.discover_shares:
                say("DISCOVER", "Reading the SMB share catalogue only; no folder contents.")
                discovered = discover_shares(host, username, password, mount_timeout)
                urls = choose_discovered_urls(discovered, mount_all=mount_all)
                results.extend(MountResult(profile.label, url, "Skipped", "Not selected.") for url in discovered if url not in urls)
        except (EOFError, KeyboardInterrupt):
            results.extend(MountResult(profile.label, url, "Cancelled", "Cancelled before mounting.") for url in urls)
            return results
        except (ConfigError, MountError) as error:
            results.extend(MountResult(profile.label, url, "Failed", str(error)) for url in urls)
            continue
        for url in urls:
            say("MOUNT", url)
            try:
                mount_volume(url, username, password, mount_timeout)
                results.append(MountResult(profile.label, url, "Mounted"))
                say("Mounted", url)
            except (MountError, ConfigError) as error:
                detail = str(error)
                if name == "work" and not confirmed:
                    detail += " If the short CCH name is unresolved, retry with --cch-server followed by the full hostname or IP address."
                results.append(MountResult(profile.label, url, "Failed", detail))
                say("Failed", detail)
            except KeyboardInterrupt:
                results.append(MountResult(profile.label, url, "Cancelled", "Mount cancelled."))
                return results
        password = None
    return results


def show_summary(results):
    print("\n  MOUNT SUMMARY\n  " + "─" * 58)
    for result in results:
        say(result.status, "{} · {}".format(result.profile, result.url))
        if result.detail:
            print("            " + safe(result.detail))
    print("\n  {} mounted · {} skipped · {} failed · {} cancelled\n".format(
        sum(r.status == "Mounted" for r in results), sum(r.status == "Skipped" for r in results),
        sum(r.status == "Failed" for r in results), sum(r.status == "Cancelled" for r in results)), flush=True)


def main():
    root = Path(os.path.abspath(__file__)).parents[2]
    parser = argparse.ArgumentParser(description="Mount home/work SMB drives sequentially with separate, private credential prompts.")
    parser.add_argument("--profile", choices=("all", "home", "work"), required=True, help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true", help="show configured drives without connecting or requesting credentials")
    parser.add_argument("--all", dest="mount_all", action="store_true", help="mount all discovered home shares without the selection menu; credentials are still requested")
    parser.add_argument("--cch-server", help="full CCH hostname or IP when the short name is unavailable; preserves the work share/subfolder")
    parser.add_argument("--config", type=Path, help="configuration file inside this project; defaults to config/mounts.local.json")
    parser.add_argument("--timeout", type=float, default=4, help="server reachability timeout in seconds (default: 4)")
    parser.add_argument("--mount-timeout", type=float, default=35, help="time limit per mount in seconds (default: 35)")
    args = parser.parse_args()
    if not (0 < args.timeout <= 60 and 0 < args.mount_timeout <= 120):
        parser.error("Use a positive reachability timeout up to 60s and mount timeout up to 120s.")
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not args.dry_run and not interactive:
        print("Run in Terminal to enter separate usernames/passwords, or use --dry-run to preview.")
        return 2
    print("\n  NETWORK DRIVES · HOME / WORK\n  Detects SMB share names; files and folders inside shares are never inspected.\n", flush=True)
    status = 1
    try:
        profiles = load_profiles(root, args.config)
        if args.cch_server is not None:
            profiles = with_cch_server(profiles, args.cch_server)
        selected = ("work", "home") if args.profile == "all" else (args.profile,)
        if args.dry_run:
            print("  PREVIEW — no connections or mount attempts.\n")
        results = run_profiles(profiles, selected, args.dry_run, args.timeout, args.mount_timeout, mount_all=args.mount_all)
        show_summary(results)
        successful = any(result.status in ("Mounted", "Preview") for result in results)
        status = 0 if successful and not any(result.status in ("Failed", "Cancelled") for result in results) else 1
    except ConfigError as error:
        say("ERROR", str(error))
        status = 2
    except KeyboardInterrupt:
        say("ERROR", "Mounting cancelled.")
        status = 130
    finally:
        if interactive and not args.dry_run:
            sys.stdout.flush()
            try:
                input("  Press Enter to close this window. ")
            except (EOFError, KeyboardInterrupt):
                pass
    return status


if __name__ == "__main__":
    sys.exit(main())
