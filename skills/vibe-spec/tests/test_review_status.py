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

from vibe_spec_core import load_spec, replace_section, validate_transition, write_spec  # noqa: E402


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

    def mark_verified(self) -> None:
        spec = load_spec(self.spec_path)
        spec.metadata["status"] = "verified"
        spec.metadata["verification_id"] = "verification-1"
        spec.body = replace_section(
            spec.body,
            "Verification Plan",
            "- Result: `python -m unittest` -> PASS (exit 0)。",
        )
        write_spec(spec)

    def test_create_review_writes_report_and_links_spec(self) -> None:
        self.mark_verified()
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
        self.assertIn("verification_id: verification-1", report)
        review_notes = load_spec(self.spec_path).body
        self.assertIn(str(report_path.relative_to(self.root)), review_notes)
        self.assertIn("PASS", review_notes)

    def test_create_review_rejects_non_verified_spec(self) -> None:
        completed = self.run_script(
            REVIEW,
            "login-flow",
            "--verdict",
            "pass",
            "--mode",
            "self",
            "--summary",
            "premature",
            "--json",
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("verified", completed.stdout)

    def test_latest_review_for_current_verification_controls_gate(self) -> None:
        self.mark_verified()
        for verdict in ("pass", "changes"):
            self.run_script(
                REVIEW,
                "login-flow",
                "--verdict",
                verdict,
                "--mode",
                "subagent",
                "--summary",
                verdict,
                "--json",
            )

        findings = validate_transition(load_spec(self.spec_path), "reviewed")

        self.assertTrue(any("审核" in finding for finding in findings))

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

    def test_review_context_uses_unique_default_paths(self) -> None:
        first = json.loads(self.run_script(CONTEXT, "login-flow", "--json").stdout)
        second = json.loads(self.run_script(CONTEXT, "login-flow", "--json").stdout)

        first_path = self.root / first["changes"][0]["path"]
        second_path = self.root / second["changes"][0]["path"]
        self.assertNotEqual(first_path, second_path)
        self.assertTrue(first_path.exists())
        self.assertTrue(second_path.exists())

    def test_review_context_refuses_existing_or_external_explicit_output(self) -> None:
        existing = self.root / ".vibe-spec" / "reports" / "owned.md"
        existing.write_text("user content\n", encoding="utf-8")
        collision = self.run_script(
            CONTEXT,
            "login-flow",
            "--output",
            str(existing),
            "--json",
            check=False,
        )
        external = self.root.parent / f"{self.root.name}-external-review.md"
        outside = self.run_script(
            CONTEXT,
            "login-flow",
            "--output",
            str(external),
            "--json",
            check=False,
        )

        self.assertNotEqual(collision.returncode, 0)
        self.assertEqual(existing.read_text(encoding="utf-8"), "user content\n")
        self.assertNotEqual(outside.returncode, 0)
        self.assertFalse(external.exists())

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
