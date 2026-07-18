from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
INIT = SKILL / "scripts" / "init_vibe_spec.py"
REFRESH = SKILL / "scripts" / "refresh_context.py"


class InitAndContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_script(self, script: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), str(self.root), *args],
            text=True,
            capture_output=True,
            check=check,
        )

    def test_minimal_init_creates_fixed_handoff_and_roadmap_entry(self) -> None:
        self.run_script(INIT, "--profile", "minimal")

        workspace = self.root / ".vibe-spec"
        self.assertTrue((workspace / "HANDOFF.md").exists())
        self.assertTrue((workspace / "ROADMAP.md").exists())
        self.assertIn("Current Goal", (workspace / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_optional_agent_entries_are_thin_and_existing_files_are_preserved(self) -> None:
        (self.root / "CLAUDE.md").write_text("user rules\n", encoding="utf-8")

        self.run_script(INIT, "--profile", "minimal", "--agent-entry", "claude", "codex")
        self.run_script(INIT, "--profile", "minimal", "--agent-entry", "claude", "codex")

        self.assertEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "user rules\n")
        codex = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".vibe-spec/HANDOFF.md", codex)
        self.assertIn(".vibe-spec/AGENT_GUIDE.md", codex)
        self.assertLess(len(codex.splitlines()), 20)

    def test_optional_ci_and_production_scripts_are_created(self) -> None:
        self.run_script(INIT, "--profile", "production", "--ci")

        self.assertTrue((self.root / ".github" / "workflows" / "vibe-spec.yml").exists())
        workflow = (self.root / ".github" / "workflows" / "vibe-spec.yml").read_text(encoding="utf-8")
        self.assertIn("unittest discover", workflow)
        scripts = self.root / ".vibe-spec" / "scripts"
        self.assertTrue((scripts / "check_vibe_spec.py").exists())
        self.assertTrue((scripts / "vibe_spec_core.py").exists())
        self.assertTrue((scripts / "update_handoff.py").stat().st_mode & 0o111)

    def test_json_init_has_stable_result_contract(self) -> None:
        completed = self.run_script(INIT, "--profile", "minimal", "--json")

        payload = json.loads(completed.stdout)
        self.assertEqual(set(payload), {"ok", "command", "changes", "findings", "next_actions"})
        self.assertTrue(payload["ok"])

    def test_refresh_context_reports_candidates_without_modifying_file_map(self) -> None:
        self.run_script(INIT, "--profile", "standard")
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
        (self.root / "package.json").write_text("{}\n", encoding="utf-8")
        file_map = self.root / ".vibe-spec" / "FILE_MAP.md"
        before = file_map.read_text(encoding="utf-8")

        completed = self.run_script(REFRESH, "--json")

        payload = json.loads(completed.stdout)
        rendered = json.dumps(payload["changes"], ensure_ascii=False)
        self.assertIn("src/", rendered)
        self.assertIn("package.json", rendered)
        self.assertEqual(file_map.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
