"""Make shortcuts dispatch existing tools without running real cleanup."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).absolute().parents[1]


class MakefileTests(unittest.TestCase):
    def test_agent_clients_run_the_selected_executable_in_the_project(self):
        with tempfile.TemporaryDirectory(prefix=".agent-launch-test-", dir=ROOT / "tests") as directory:
            fixture = Path(directory)
            binary = fixture / "client with spaces"
            binary.write_text(
                '#!/usr/bin/python3\nimport json, os, sys\n'
                'from pathlib import Path\n'
                'Path(os.environ["AGENT_LAUNCH_RESULT"]).write_text('
                'json.dumps({"cwd": os.getcwd(), "args": sys.argv[1:]}))\n')
            binary.chmod(0o755)
            for target, variable in (("agent", "AGENT"), ("gemini", "GEMINI")):
                with self.subTest(target=target):
                    output = fixture / (target + ".json")
                    settings = os.environ.copy()
                    settings["AGENT_LAUNCH_RESULT"] = str(output)
                    result = subprocess.run(["make", target, variable + "=" + str(binary)],
                                            cwd=ROOT, env=settings, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(output.read_text()), {"cwd": str(ROOT), "args": []})

    def test_make_cleanup_aliases_only_dispatch_the_selected_script(self):
        for kind in ("cache", "logs"):
            result = subprocess.run(["make", "-n", "clear", kind], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("./clear-" + kind + ".sh"), 1)
            other = "logs" if kind == "cache" else "cache"
            self.assertNotIn("./clear-" + other + ".sh", result.stdout)
            self.assertNotIn("--yes", result.stdout)


if __name__ == "__main__":
    unittest.main()
