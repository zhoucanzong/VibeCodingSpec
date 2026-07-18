from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vibe_spec_core import load_spec, today, write_spec  # noqa: E402


INIT = SCRIPTS / "init_vibe_spec.py"
CREATE = SCRIPTS / "create_spec.py"
CHECK = SCRIPTS / "check_vibe_spec.py"
HOOKS = SCRIPTS / "install_git_hooks.py"


class CheckAndHooksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.run_script(INIT, "--profile", "standard")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_script(
        self,
        script: Path,
        *args: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), str(self.root), *args],
            text=True,
            capture_output=True,
            check=check,
        )

    def create(self, spec_id: str, parent: str = "project") -> None:
        self.run_script(CREATE, spec_id, "--title", spec_id, "--parent", parent)

    def test_json_check_has_stable_contract(self) -> None:
        completed = self.run_script(CHECK, "--json")

        payload = json.loads(completed.stdout)
        self.assertEqual(set(payload), {"ok", "command", "changes", "findings", "next_actions"})

    def test_check_detects_unindexed_and_orphan_index_rows(self) -> None:
        self.create("login-flow")
        index = self.root / ".vibe-spec" / "SPEC_INDEX.md"
        text = index.read_text(encoding="utf-8")
        text = text.replace("| login-flow |", "| orphan-flow |")
        index.write_text(text, encoding="utf-8")

        completed = self.run_script(CHECK, "--strict", "--json", check=False)
        codes = {finding["code"] for finding in json.loads(completed.stdout)["findings"]}

        self.assertIn("unindexed_spec", codes)
        self.assertIn("orphan_index_entry", codes)

    def test_check_detects_duplicate_ids_and_broken_references(self) -> None:
        self.create("base-flow")
        specs = self.root / ".vibe-spec" / "specs"
        original = next(specs.glob("*base-flow.md"))
        duplicate = specs / "2026-07-18-duplicate.md"
        duplicate.write_text(
            original.read_text(encoding="utf-8").replace("parent: project", "parent: missing-parent"),
            encoding="utf-8",
        )

        completed = self.run_script(CHECK, "--strict", "--json", check=False)
        codes = {finding["code"] for finding in json.loads(completed.stdout)["findings"]}

        self.assertIn("duplicate_spec_id", codes)
        self.assertIn("broken_parent", codes)

    def test_check_reports_incomplete_handoff(self) -> None:
        completed = self.run_script(CHECK, "--strict", "--json", check=False)
        findings = json.loads(completed.stdout)["findings"]

        self.assertTrue(any(item["code"] == "incomplete_handoff" for item in findings))

    def test_check_detects_index_status_and_lifecycle_evidence_drift(self) -> None:
        self.create("login-flow")
        path = next((self.root / ".vibe-spec" / "specs").glob("*login-flow.md"))
        spec = load_spec(path)
        spec.metadata["status"] = "approved"
        write_spec(spec)

        completed = self.run_script(CHECK, "--strict", "--json", check=False)
        codes = {finding["code"] for finding in json.loads(completed.stdout)["findings"]}

        self.assertIn("index_status_mismatch", codes)
        self.assertIn("missing_lifecycle_evidence", codes)

    def test_check_detects_index_path_and_roadmap_reference_drift(self) -> None:
        self.create("login-flow")
        index = self.root / ".vibe-spec" / "SPEC_INDEX.md"
        index.write_text(
            index.read_text(encoding="utf-8").replace(f"specs/{today()}-login-flow.md", "specs/wrong.md"),
            encoding="utf-8",
        )
        roadmap = self.root / ".vibe-spec" / "ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "| none | none | idea | 暂无已确认计划 |",
                "| Ghost feature | missing-spec | planned | invalid reference |",
            ),
            encoding="utf-8",
        )

        completed = self.run_script(CHECK, "--strict", "--json", check=False)
        codes = {finding["code"] for finding in json.loads(completed.stdout)["findings"]}

        self.assertIn("index_path_mismatch", codes)
        self.assertIn("broken_roadmap_spec", codes)

    def test_hook_installer_refuses_unmanaged_hook_without_modifying_it(self) -> None:
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        hook = self.root / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho user-hook\n", encoding="utf-8")
        before = hook.read_text(encoding="utf-8")

        completed = self.run_script(HOOKS, "--json", check=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(hook.read_text(encoding="utf-8"), before)

    def test_hook_installer_creates_managed_executable_hooks(self) -> None:
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)

        completed = self.run_script(HOOKS, "--json")
        payload = json.loads(completed.stdout)

        self.assertTrue(payload["ok"])
        for name in ("pre-commit", "pre-push"):
            hook = self.root / ".git" / "hooks" / name
            self.assertTrue(hook.exists())
            self.assertTrue(hook.stat().st_mode & 0o111)
            self.assertIn("managed-by-vibe-spec", hook.read_text(encoding="utf-8"))

    def test_force_hook_install_preflights_all_backups_before_mutation(self) -> None:
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        hooks = self.root / ".git" / "hooks"
        pre_commit = hooks / "pre-commit"
        pre_push = hooks / "pre-push"
        pre_commit.write_text("#!/bin/sh\necho first\n", encoding="utf-8")
        pre_push.write_text("#!/bin/sh\necho second\n", encoding="utf-8")
        (hooks / "pre-push.pre-vibe-spec").write_text("existing backup\n", encoding="utf-8")

        completed = self.run_script(HOOKS, "--force", "--json", check=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("echo first", pre_commit.read_text(encoding="utf-8"))
        self.assertIn("echo second", pre_push.read_text(encoding="utf-8"))

    def test_hook_installer_preserves_existing_project_check_script(self) -> None:
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        scripts = self.root / ".vibe-spec" / "scripts"
        scripts.mkdir(parents=True)
        custom = scripts / "check_vibe_spec.py"
        custom.write_text("# project-owned check\n", encoding="utf-8")

        self.run_script(HOOKS, "--json")

        self.assertEqual(custom.read_text(encoding="utf-8"), "# project-owned check\n")

    def test_hook_installer_uses_common_git_dir_from_linked_worktree(self) -> None:
        main = self.root / "main"
        linked = self.root / "linked"
        main.mkdir()
        subprocess.run([sys.executable, str(INIT), str(main), "--profile", "minimal"], check=True, capture_output=True)
        subprocess.run(["git", "init", str(main)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(main), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(main), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(main), "add", "."], check=True)
        subprocess.run(["git", "-C", str(main), "commit", "-m", "fixture"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(main), "worktree", "add", "-b", "linked-test", str(linked)], check=True, capture_output=True)

        completed = subprocess.run(
            [sys.executable, str(HOOKS), str(linked), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertTrue(json.loads(completed.stdout)["ok"])
        common_hook = main / ".git" / "hooks" / "pre-commit"
        wrong_hook = main / ".git" / "worktrees" / "linked" / "hooks" / "pre-commit"
        self.assertIn("managed-by-vibe-spec", common_hook.read_text(encoding="utf-8"))
        self.assertFalse(wrong_hook.exists())
        sibling_commit = subprocess.run(
            ["git", "-C", str(main), "commit", "--allow-empty", "-m", "sibling hook check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(sibling_commit.returncode, 0, sibling_commit.stderr + sibling_commit.stdout)


if __name__ == "__main__":
    unittest.main()
