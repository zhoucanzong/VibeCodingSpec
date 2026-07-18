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

from vibe_spec_core import load_spec, replace_section, write_spec  # noqa: E402


INIT = SCRIPTS / "init_vibe_spec.py"
CREATE = SCRIPTS / "create_spec.py"
REVIEW = SCRIPTS / "create_review.py"
CONTEXT = SCRIPTS / "prepare_review_context.py"
STATUS = SCRIPTS / "status_vibe_spec.py"
HANDOFF = SCRIPTS / "update_handoff.py"


class ReviewStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.run_script(INIT, "--profile", "standard")
        created = self.run_script(CREATE, "login-flow", "--title", "Login Flow", "--json")
        payload = json.loads(created.stdout)
        self.spec_path = self.root / payload["changes"][0]["path"]

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

    def test_create_review_writes_report_and_links_spec(self) -> None:
        completed = self.run_script(
            REVIEW,
            "login-flow",
            "--verdict",
            "pass",
            "--mode",
            "subagent",
            "--summary",
            "验收标准全部满足",
            "--finding",
            "P2: 可以补充性能样本",
            "--json",
        )
        payload = json.loads(completed.stdout)

        report_path = self.root / payload["changes"][0]["path"]
        self.assertTrue(report_path.exists())
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("mode: subagent", report)
        self.assertIn("verdict: pass", report)
        review_notes = load_spec(self.spec_path).body
        self.assertIn(str(report_path.relative_to(self.root)), review_notes)
        self.assertIn("PASS", review_notes)

    def test_review_context_excludes_implementation_and_review_conclusions(self) -> None:
        spec = load_spec(self.spec_path)
        spec.body = replace_section(spec.body, "Requirements", "- 必须登录。")
        spec.body = replace_section(spec.body, "Implementation Notes", "SECRET IMPLEMENTER CONCLUSION")
        spec.body = replace_section(spec.body, "Review Notes", "SECRET REVIEW CONCLUSION")
        write_spec(spec)

        completed = self.run_script(CONTEXT, "login-flow", "--json")
        payload = json.loads(completed.stdout)
        context_path = self.root / payload["changes"][0]["path"]
        context = context_path.read_text(encoding="utf-8")

        self.assertIn("必须登录", context)
        self.assertNotIn("SECRET IMPLEMENTER CONCLUSION", context)
        self.assertNotIn("SECRET REVIEW CONCLUSION", context)

    def test_update_handoff_replaces_owned_sections_and_preserves_links(self) -> None:
        completed = self.run_script(
            HANDOFF,
            "--goal",
            "完成登录流程",
            "--state",
            "in_progress",
            "--active-spec",
            "login-flow",
            "--verification",
            "unit tests: PASS",
            "--next-action",
            "执行独立 review",
            "--json",
        )
        self.assertTrue(json.loads(completed.stdout)["ok"])

        handoff = (self.root / ".vibe-spec" / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("完成登录流程", handoff)
        self.assertIn("login-flow", handoff)
        self.assertIn("执行独立 review", handoff)
        self.assertIn("Context Links", handoff)

    def test_status_json_summarizes_specs_handoff_and_roadmap(self) -> None:
        self.run_script(
            HANDOFF,
            "--goal",
            "完成登录流程",
            "--state",
            "in_progress",
            "--active-spec",
            "login-flow",
            "--next-action",
            "继续实现",
        )

        completed = self.run_script(STATUS, "--json")
        payload = json.loads(completed.stdout)
        summary = payload["changes"][0]

        self.assertEqual(summary["states"]["draft"], 1)
        self.assertEqual(summary["current_goal"], "完成登录流程")
        self.assertIn("login-flow", summary["active_specs"])
        self.assertIn("建立项目上下文", summary["roadmap_now"])


if __name__ == "__main__":
    unittest.main()
