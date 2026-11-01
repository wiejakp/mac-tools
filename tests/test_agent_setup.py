"""Agent setup tests use disposable local fixtures, never the real agent home."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).absolute().parents[1]
MODULE = ROOT / "src/local_scripts/agent_setup.py"


class PluginRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".agent-setup-test-", dir=ROOT / "tests")
        self.base = Path(self.temp.name)
        self.plugin = self.base / "plugin"
        self.bin = self.plugin / "node_modules/.bin"
        self.bin.mkdir(parents=True)
        self.target = self.plugin / "node_modules/tool/cli.sh"
        self.target.parent.mkdir()
        self.target.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n', encoding="utf-8")
        self.target.chmod(0o755)
        self.link = self.bin / "tool"
        self.link.symlink_to("../tool/cli.sh")
        self.backup = self.base / "backups"

    def tearDown(self):
        self.temp.cleanup()

    def repair(self, apply=False):
        self.assertTrue(MODULE.is_file(), "Repeatable safe plugin repair is missing")
        spec = importlib.util.spec_from_file_location("agent_setup", MODULE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module.repair_plugin(self.plugin, self.backup, apply)

    def test_preview_leaves_plugin_and_backup_untouched(self):
        changes = self.repair()
        self.assertEqual(len(changes), 1)
        self.assertTrue(self.link.is_symlink())
        self.assertFalse(self.backup.exists())

    def test_forwarder_preserves_arguments_and_original_target(self):
        original = self.target.read_bytes()
        self.repair(apply=True)
        self.assertFalse(self.link.is_symlink())
        result = subprocess.run([str(self.link), "two words", "$(no-execution)", ""],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "two words\n$(no-execution)\n\n")
        self.assertEqual(self.target.read_bytes(), original)
        saved = list(self.backup.glob("*.json"))
        self.assertEqual(len(saved), 1)
        record = json.loads(saved[0].read_text())
        self.assertEqual(record["links"][0]["target"], "../tool/cli.sh")

    def test_second_repair_does_not_rewrite_or_create_backup(self):
        self.repair(apply=True)
        before = self.link.stat().st_mtime_ns
        self.assertEqual(self.repair(apply=True), [])
        self.assertEqual(self.link.stat().st_mtime_ns, before)
        self.assertEqual(len(list(self.backup.glob("*.json"))), 1)

    def test_escaping_link_rejects_entire_repair_before_mutation(self):
        external = self.base / "outside"
        external.write_text("must stay untouched")
        (self.bin / "escape").symlink_to(external)
        with self.assertRaisesRegex(ValueError, "outside"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())
        self.assertFalse(self.backup.exists())

    def test_broken_link_rejected_without_mutation(self):
        (self.bin / "broken").symlink_to("../missing")
        with self.assertRaisesRegex(ValueError, "missing|broken"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())

    def test_link_outside_npm_bin_is_not_rewritten(self):
        (self.plugin / "unexpected").symlink_to("node_modules/tool/cli.sh")
        with self.assertRaisesRegex(ValueError, "unexpected|npm"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())

    def test_symlink_plugin_root_is_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.plugin, target_is_directory=True)
        self.plugin = alias
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.repair(apply=True)

    def test_non_executable_target_is_rejected(self):
        self.target.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "executable"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())

    def test_absolute_internal_link_still_executes(self):
        self.link.unlink()
        self.link.symlink_to(self.target)
        self.repair(apply=True)
        result = subprocess.run([str(self.link), "argument"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "argument\n")

    def test_symlinked_plugin_ancestor_is_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.base, target_is_directory=True)
        self.plugin = alias / "plugin"
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())

    def test_symlinked_backup_directory_is_rejected(self):
        outside = self.base / "other-backups"
        outside.mkdir()
        self.backup.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.repair(apply=True)
        self.assertTrue(self.link.is_symlink())
        self.assertEqual(list(outside.iterdir()), [])


class SharedSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".agent-setup-test-", dir=ROOT / "tests")
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.repo = self.base / "repo"
        self.original = self.home / ".codex/skills/example/SKILL.md"
        self.original.parent.mkdir(parents=True)
        self.original.write_text("Original skill\n")
        system = self.home / ".codex/skills/.system/internal"
        system.mkdir(parents=True)
        (system / "SKILL.md").write_text("Managed skill\n")
        helper = self.repo / ".agents/skills/mac-helper/SKILL.md"
        helper.parent.mkdir(parents=True)
        helper.write_text("Portable helper\n")
        instructions = self.repo / ".agents/skills/mac-helper/references/shared-instructions.md"
        instructions.parent.mkdir()
        instructions.write_text("Shared local agent guidance\n")
        (self.home / ".codex/AGENTS.md").write_text("Keep existing rules\n")

    def tearDown(self):
        self.temp.cleanup()

    def install(self, apply=False):
        spec = importlib.util.spec_from_file_location("agent_setup", MODULE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "install_shared_skills"), "Shared skill installation is missing")
        return module.install_shared_skills(self.home, self.repo, apply)

    def test_preview_keeps_original_paths_and_contents(self):
        self.assertTrue(self.install())
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse(self.original.parent.is_symlink())
        self.assertEqual(self.original.read_text(), "Original skill\n")

    def test_agents_read_and_edit_the_same_skill(self):
        self.install(apply=True)
        shared = self.home / ".agents/skills/example/SKILL.md"
        self.assertTrue(self.original.parent.is_symlink())
        for agent in (".codex", ".claude", ".gemini"):
            candidate = self.home / agent / "skills/example/SKILL.md"
            self.assertTrue(os.path.samefile(candidate, shared))
        (self.home / ".claude/skills/example/SKILL.md").write_text("One shared update\n")
        self.assertEqual(self.original.read_text(), "One shared update\n")
        self.assertEqual((self.home / ".gemini/skills/example/SKILL.md").read_text(), "One shared update\n")
        self.assertFalse((self.home / ".codex/skills/.system").is_symlink())

    def test_repeated_install_does_not_duplicate_instructions_or_backups(self):
        self.install(apply=True)
        original = (self.home / ".codex/AGENTS.md").read_bytes()
        backups = list((self.home / ".agents/backups").iterdir())
        self.assertEqual(self.install(apply=True), [])
        self.assertEqual((self.home / ".codex/AGENTS.md").read_bytes(), original)
        self.assertEqual(list((self.home / ".agents/backups").iterdir()), backups)

    def test_conflicting_skill_rejects_before_any_change(self):
        conflict = self.home / ".agents/skills/example"
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("Other skill\n")
        with self.assertRaisesRegex(ValueError, "conflict|collision"):
            self.install(apply=True)
        self.assertFalse(self.original.parent.is_symlink())
        self.assertEqual((conflict / "SKILL.md").read_text(), "Other skill\n")
        self.assertFalse((self.home / ".agents/backups").exists())

    def test_existing_claude_skills_and_rules_are_preserved(self):
        other = self.home / ".claude/skills/second/SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_text("Claude personal skill\n")
        rules = self.home / ".claude/CLAUDE.md"
        rules.write_text("Keep Claude rules\n")
        self.install(apply=True)
        self.assertEqual(other.read_text(), "Claude personal skill\n")
        self.assertEqual((self.home / ".agents/skills/second/SKILL.md").read_text(), "Claude personal skill\n")
        self.assertIn("Keep Claude rules", rules.read_text())
        self.assertIn("Keep existing rules", (self.home / ".codex/AGENTS.md").read_text())
        self.assertTrue((self.home / ".claude/skills/example/SKILL.md").is_file())
        self.assertTrue((self.home / ".claude/skills/mac-helper/SKILL.md").is_file())
        added = self.home / ".agents/skills/later/SKILL.md"
        added.parent.mkdir()
        added.write_text("Later shared skill\n")
        self.assertEqual((self.home / ".claude/skills/later/SKILL.md").read_text(), "Later shared skill\n")

    def test_inventory_does_not_follow_an_existing_report_link(self):
        spec = importlib.util.spec_from_file_location("agent_setup", MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "write_inventory"), "Safe inventory write is missing")
        target = self.base / "unrelated.txt"
        target.write_text("Keep this data")
        report = self.repo / "report.json"
        report.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symlink"):
            module.write_inventory(report, {"fixture": True})
        self.assertEqual(target.read_text(), "Keep this data")

    def test_unexpected_agent_skill_root_symlink_is_not_followed(self):
        outside = self.base / "unapproved"
        outside.mkdir()
        (self.home / ".claude").mkdir()
        (self.home / ".claude/skills").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink|outside"):
            self.install(apply=True)
        self.assertFalse(self.original.parent.is_symlink())


if __name__ == "__main__":
    unittest.main()
