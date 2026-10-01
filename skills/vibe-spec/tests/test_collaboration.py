from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collaboration_core import inspect_collaboration
from init_vibe_spec import init_workspace, install_ci
from vibe_spec_core import render_frontmatter


class CollaborationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        init_workspace(self.root, "minimal", ["collaboration"])
        self.workspace = self.root / ".vibe-spec"
        self.collab = self.workspace / "collaboration"
        self.write("TEAM.md", {"coordinator": "boss", "rules_revision": "rules-v1"})
        self.write("agents/boss.md", {"agent_id": "boss", "role": "coordinator",
                   "status": "local", "transport": "self", "rules_revision": "rules-v1"})
        self.agent()
        (self.workspace / "specs" / "orders.md").write_text(
            render_frontmatter({"spec_id": "orders", "status": "draft"}), encoding="utf-8")

    def write(self, relative, data, body="真实接收内容及工具来源记录。\n"):
        path = self.collab / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_frontmatter(data) + body, encoding="utf-8")
        return path

    def agent(self, endpoint="thread-a", status="connected"):
        self.write("agents/api.md", {"agent_id": "api", "role": "lead", "status": status,
                   "transport": "native", "endpoint": endpoint, "workspace": "/repo/api",
                   "hello_message": "hello-a", "hello_ack": "collaboration/messages/ack-a.md",
                   "rules_revision": "rules-v1"})
        self.write("messages/ack-a.md", {"message_id": "ack-a", "kind": "hello_ack",
                   "sender": "api", "recipient": "boss", "reply_to": "hello-a",
                   "revision": "rules-v1", "endpoint": "thread-a"})

    def task(self, identifier="api-task", **overrides):
        data = {"task_id": identifier, "stream": "backend", "spec_id": "orders",
                "owner": "api", "acceptor": "boss", "status": "running", "depends_on": [],
                "base_revision": "commit-a", "rules_revision": "rules-v1", "workspace": "/repo/api",
                "write_scope": ["src/api"], "deliverable_revision": "commit-b",
                "acceptance": "collaboration/messages/accepted.md"}
        data.update(overrides)
        body = "## Goal\n\n完成订单 API\n\n## Acceptance Criteria\n\n订单可查询\n\n## Verification\n\n- Result: `pytest` -> PASS (exit 0)\n\n## Result\n\n订单查询已交付，修改 src/api。\n"
        return self.write(f"tasks/{identifier}.md", data, body)

    def codes(self):
        return {item["code"] for item in inspect_collaboration(self.workspace)[1]}

    def test_connected_team_and_running_task_are_valid(self):
        self.task()
        self.assertEqual(self.codes(), set())

    def test_unanswered_invitation_cannot_receive_running_task(self):
        self.agent(status="invited")
        self.task()
        self.assertIn("unconnected_task_agent", self.codes())

    def test_changed_endpoint_invalidates_old_handshake(self):
        self.agent(endpoint="new-thread")
        self.assertIn("missing_hello_ack", self.codes())

    def test_missing_receipt_does_not_count_as_connected(self):
        (self.collab / "messages/ack-a.md").unlink()
        self.assertIn("missing_hello_ack", self.codes())

    def test_new_rules_require_member_and_task_sync(self):
        self.task()
        self.write("TEAM.md", {"coordinator": "boss", "rules_revision": "rules-v2"})
        self.assertTrue({"agent_rules_drift", "task_rules_drift", "missing_hello_ack"} <= self.codes())

    def test_subtree_overlap_even_across_worktrees_is_reported(self):
        self.task()
        self.task("second", write_scope=["src/api/routes.py"], workspace="/another-worktree")
        self.assertIn("overlapping_write_scope", self.codes())

    def test_not_started_dependency_wait_does_not_reserve_scope(self):
        self.task()
        self.task("second", status="blocked", execution_state="not_started", depends_on=["api-task"])
        self.assertNotIn("overlapping_write_scope", self.codes())
        self.task("second", status="blocked", execution_state="may_be_running", depends_on=["api-task"])
        self.assertIn("overlapping_write_scope", self.codes())

    def test_old_runtime_requires_explicit_upgrade_and_preserves_backup(self):
        init_workspace(self.root, "minimal", ["scripts"])
        check = self.workspace / "scripts/check_vibe_spec.py"
        original = "print('old checker')\n"
        check.write_text(original, encoding="utf-8")
        before = (self.workspace / "MODULES.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "refresh-runtime"):
            init_workspace(self.root, "minimal", ["collaboration"])
        self.assertEqual(check.read_text(encoding="utf-8"), original)

        self.assertEqual((self.workspace / "MODULES.md").read_bytes(), before)
        init_workspace(self.root, "minimal", ["collaboration"], upgrade_runtime=True)
        self.assertEqual(check.with_name(check.name + ".pre-vibe-spec").read_text(encoding="utf-8"), original)
        self.task(owner="missing")
        result = subprocess.run([sys.executable, str(check), str(self.root), "--strict", "--json"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("unknown_task_agent", {f["code"] for f in json.loads(result.stdout)["findings"]})
        check.write_text(original, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "备份已存在"):
            init_workspace(self.root, "minimal", ["collaboration"], upgrade_runtime=True)
        self.assertEqual(check.read_text(encoding="utf-8"), original)

    def test_minimal_ci_upgrade_installs_complete_runtime(self):
        install_ci(self.root)
        scripts = self.workspace / "scripts"
        (scripts / "check_vibe_spec.py").write_text("print('legacy CI')\n", encoding="utf-8")
        (scripts / "collaboration_core.py").unlink()
        init_workspace(self.root, "minimal", ["collaboration"], upgrade_runtime=True)
        self.assertTrue((scripts / "collaboration_core.py").exists())
        self.assertTrue((self.workspace / "assets/templates/COLLABORATION.md").exists())
        result = subprocess.run([sys.executable, str(scripts / "status_vibe_spec.py"),
                                 str(self.root), "--json"], text=True, capture_output=True, check=True)
        self.assertIn("collaboration", json.loads(result.stdout)["changes"][0])

    def test_runtime_upgrade_failure_restores_content_and_executable_modes(self):
        init_workspace(self.root, "minimal", ["scripts"])
        checker = self.workspace / "scripts/check_vibe_spec.py"
        core = self.workspace / "scripts/vibe_spec_core.py"
        originals = {checker: "print('old checker')\n", core: "print('old core')\n"}
        for path, body in originals.items():
            path.write_text(body, encoding="utf-8")
            path.chmod(0o755)
        replace = Path.replace
        injected = False

        def fail_once(path, target):
            nonlocal injected
            if Path(target) == core and not injected:
                injected = True
                raise OSError("simulated replace failure")
            return replace(path, target)

        with patch.object(Path, "replace", fail_once):
            with self.assertRaisesRegex(OSError, "simulated"):
                init_workspace(self.root, "minimal", ["collaboration"], upgrade_runtime=True)
        for path, body in originals.items():
            self.assertEqual(path.read_text(encoding="utf-8"), body)
            self.assertEqual(path.stat().st_mode & 0o777, 0o755)
            self.assertFalse(path.with_name(path.name + ".pre-vibe-spec").exists())

    def test_dependency_cycle_and_unaccepted_dependency_are_reported(self):
        self.task(depends_on=["second"])
        self.task("second", depends_on=["api-task"], write_scope=[])
        self.assertTrue({"task_dependency_cycle", "unfinished_dependency"} <= self.codes())

    def test_acceptance_is_bound_to_deliverable_and_acceptor(self):
        self.task(status="accepted")
        self.assertIn("missing_task_acceptance", self.codes())
        self.write("messages/accepted.md", {"message_id": "accepted", "kind": "acceptance",
                   "sender": "boss", "recipient": "api", "task_id": "api-task",
                   "revision": "commit-b", "rules_revision": "rules-v1", "verdict": "pass"})
        self.assertEqual(self.codes(), set())
        self.task(status="accepted", rules_revision="rules-v2")
        self.assertIn("missing_task_acceptance", self.codes())
        self.task(status="accepted", deliverable_revision="commit-c")
        self.assertIn("missing_task_acceptance", self.codes())
        self.task(status="accepted", acceptor="api")
        self.assertIn("self_acceptance", self.codes())

    def test_invalid_metadata_returns_findings_not_crash(self):
        self.task(status=["running"])
        self.assertIn("invalid_collaboration_record", self.codes())

    def test_future_verification_text_cannot_pass_acceptance(self):
        path = self.task(status="accepted")
        text = path.read_text(encoding="utf-8").replace(
            "- Result: `pytest` -> PASS (exit 0)", "计划稍后运行 pytest")
        path.write_text(text, encoding="utf-8")
        self.assertIn("missing_task_verification", self.codes())

    def test_enable_updates_custom_module_table_without_losing_notes(self):
        path = self.workspace / "MODULES.md"
        path.write_text("# 自定义模块\n\n| 模块 | 是否启用 | 备注 |\n|---|---|---|\n"
                        "| core | yes | 我的说明 |\n| collaboration | no | 团队试用 |\n",
                        encoding="utf-8")
        init_workspace(self.root, "minimal", ["collaboration"])
        text = path.read_text(encoding="utf-8")
        self.assertIn("| collaboration | yes | 团队试用 |", text)
        self.assertIn("我的说明", text)

    def test_path_escape_and_missing_owner_are_reported(self):
        self.task(owner="missing", write_scope=["../secret"])
        self.assertTrue({"unknown_task_agent", "invalid_write_scope"} <= self.codes())

    def test_module_is_optional_and_enabling_preserves_previous_modules(self):
        self.assertFalse((self.workspace / "DATA_GUIDE.md").exists())
        init_workspace(self.root, "minimal", ["data"])
        init_workspace(self.root, "minimal", ["collaboration"])
        modules = (self.workspace / "MODULES.md").read_text(encoding="utf-8")
        self.assertIn("| data | yes |", modules)
        self.assertIn("| collaboration | yes |", modules)
        self.assertIn("coordinator: boss", (self.collab / "TEAM.md").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as fresh:
            init_workspace(Path(fresh), "production", [])
            self.assertFalse((Path(fresh) / ".vibe-spec/collaboration").exists())

    def test_deployed_ci_runtime_checks_collaboration_and_status(self):
        self.task(owner="missing")
        install_ci(self.root)
        command = [sys.executable, str(self.workspace / "scripts/check_vibe_spec.py"),
                   str(self.root), "--strict", "--json"]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("unknown_task_agent", {f["code"] for f in json.loads(result.stdout)["findings"]})
        init_workspace(self.root, "minimal", ["scripts"])
        result = subprocess.run([sys.executable, str(self.workspace / "scripts/status_vibe_spec.py"),
                                 str(self.root), "--json"], text=True, capture_output=True, check=True)
        summary = json.loads(result.stdout)["changes"][0]["collaboration"]
        self.assertEqual(summary["coordinator"], "boss")
        self.assertEqual(summary["tasks"], {"running": 1})


if __name__ == "__main__":
    unittest.main()
