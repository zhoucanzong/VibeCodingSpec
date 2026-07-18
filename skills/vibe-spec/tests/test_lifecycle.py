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
PROMOTE = SCRIPTS / "promote_spec.py"


class LifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.run_script(INIT, "--profile", "minimal")

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

    def create(self, spec_id: str = "login-flow") -> Path:
        completed = self.run_script(CREATE, spec_id, "--title", "Login Flow", "--json")
        payload = json.loads(completed.stdout)
        return self.root / payload["changes"][0]["path"]

    def make_spec_ready(self, path: Path) -> None:
        spec = load_spec(path)
        content = {
            "Summary": "实现稳定的登录流程。",
            "Context": "用户需要安全登录。",
            "Goals": "- 支持邮箱登录。",
            "Requirements": "- 登录成功后创建会话。",
            "Acceptance Criteria": "- [ ] 有效用户可以登录。",
            "Verification Plan": "- 运行登录测试并记录通过结果。",
        }
        body = spec.body
        for heading, value in content.items():
            body = replace_section(body, heading, value)
        spec.body = body
        write_spec(spec)

    def promote(self, spec_id: str, state: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_script(
            PROMOTE,
            spec_id,
            state,
            "--reason",
            f"move to {state}",
            "--evidence",
            "test evidence",
            "--json",
            check=check,
        )

    def test_create_normalizes_id_and_updates_index(self) -> None:
        completed = self.run_script(CREATE, "Login Flow", "--title", "Login Flow", "--json")
        payload = json.loads(completed.stdout)

        path = self.root / payload["changes"][0]["path"]
        self.assertTrue(path.exists())
        self.assertEqual(load_spec(path).spec_id, "login-flow")
        index = (self.root / ".vibe-spec" / "SPEC_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("login-flow", index)

    def test_duplicate_id_is_rejected(self) -> None:
        self.create()

        completed = self.run_script(CREATE, "login-flow", "--title", "Duplicate", "--json", check=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("已存在", completed.stdout)

    def test_illegal_transition_does_not_modify_spec(self) -> None:
        path = self.create()
        before = path.read_text(encoding="utf-8")

        completed = self.promote("login-flow", "active", check=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_content_gate_blocks_incomplete_draft_without_writes(self) -> None:
        path = self.create()
        before = path.read_text(encoding="utf-8")

        completed = self.promote("login-flow", "ready_for_review", check=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Acceptance Criteria", completed.stdout)
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_valid_transition_updates_spec_log_and_index(self) -> None:
        path = self.create()
        self.make_spec_ready(path)

        self.promote("login-flow", "ready_for_review")

        spec = load_spec(path)
        self.assertEqual(spec.status, "ready_for_review")
        self.assertIn("`draft` -> `ready_for_review`", spec.body)
        index = (self.root / ".vibe-spec" / "SPEC_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("| ready_for_review |", index)

    def test_implemented_and_verified_gates_require_evidence(self) -> None:
        path = self.create()
        self.make_spec_ready(path)
        for state in ("ready_for_review", "approved", "in_progress"):
            self.promote("login-flow", state)

        failed = self.promote("login-flow", "implemented", check=False)
        self.assertNotEqual(failed.returncode, 0)

        spec = load_spec(path)
        spec.body = replace_section(spec.body, "Implementation Notes", "- 完成 `src/login.py`。")
        write_spec(spec)
        self.promote("login-flow", "implemented")

        failed = self.promote("login-flow", "verified", check=False)
        self.assertNotEqual(failed.returncode, 0)
        spec = load_spec(path)
        spec.body = replace_section(spec.body, "Verification Plan", "- `python -m unittest`: PASS, exit 0。")
        write_spec(spec)
        self.promote("login-flow", "verified")
        self.assertEqual(load_spec(path).status, "verified")


if __name__ == "__main__":
    unittest.main()
