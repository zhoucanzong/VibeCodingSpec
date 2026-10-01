from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from create_experiment import create_record
from experiment_core import conclusion_digest, digest_file, inspect_experiments, read_record
from init_vibe_spec import init_workspace, install_ci
from vibe_spec_core import SpecError, render_frontmatter, replace_section
from work_records import record_lock, record_work


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        init_workspace(self.root, "minimal", ["experiments"])
        self.workspace = self.root / ".vibe-spec"
        self.plan = create_record(self.root, "EXP-001", "plan", None, "researcher", "检索对比")

    def update(self, path, metadata=None, sections=None):
        data, body = read_record(path)
        data.update(metadata or {})
        for heading, text in (sections or {}).items():
            body = replace_section(body, heading, text)
        path.write_text(render_frontmatter(data) + body, encoding="utf-8")

    def ready_plan(self):
        self.update(self.plan, {"status": "running"},
                    {heading: "预先约定的实验设计与判定规则" for heading in
                     ("Question", "Hypothesis", "Design", "Decision Rule", "Budget")})

    def completed_run(self, run_id="RUN-001", state="completed"):
        self.ready_plan()
        path = create_record(self.root, "EXP-001", "run", run_id, "researcher")
        artifact = self.root / f"{run_id}-metrics.json"
        artifact.write_text('{"recall": 0.5}\n', encoding="utf-8")
        self.update(path, {"status": state, "started": "2026-10-02T00:00:00Z",
                    "ended": "2026-10-02T00:01:00Z", "code_revision": "commit-a",
                    "data_version": "dataset-v1", "model": "test-model-v1", "seed": "42",
                    "exit_code": "0" if state == "completed" else "1", "artifacts_status": "available"},
                    {"Configuration": "top_k=10; seed=42", "Environment": "Python 3",
                     "Command": "python evaluate.py", "Metrics": "Recall@10=0.5",
                     "Observations": "低于基线，保留负结果", "Limitations": "只覆盖固定测试集",
                     "Artifacts": f"| Path | SHA256 | Purpose |\n|---|---|---|\n| {artifact.name} | {digest_file(artifact)} | 原始指标 |"})
        return path, artifact

    def reviewed_conclusion(self, cid="CON-001", supersedes="none"):
        path = create_record(self.root, "EXP-001", "conclusion", cid, "lead")
        report = self.workspace / "reports" / f"{cid}.md"
        report.parent.mkdir(exist_ok=True)
        self.update(path, {"status": "reviewed", "reviewer": "reviewer", "review_mode": "independent",
                           "decision": "reject", "supersedes": supersedes,
                           "review_evidence": report.relative_to(self.root).as_posix()},
                    {heading: "已核对基线、失败与负结果，当前证据不足以采用。" for heading in
                     ("Analysis", "Limitations", "Decision Impact", "Review")})
        data, body = read_record(path)
        report.write_text(render_frontmatter({"experiment_id": "EXP-001", "conclusion_id": cid,
                          "conclusion_sha256": conclusion_digest(data, body), "reviewer": "reviewer",
                          "review_mode": "independent", "verdict": "pass"}) +
                          "## Findings\n\n未发现阻塞问题，已核对全部runs。\n\n## Assessment\n\n基线与失败均保留，结论与证据一致。\n", encoding="utf-8")
        return path

    def codes(self, verify=False):
        return {f["code"] for f in inspect_experiments(self.workspace, verify)[1]}

    def test_rejects_duplicate_plan_and_preserves_index(self):
        before = (self.workspace / "EXPERIMENTS.md").read_bytes()
        with self.assertRaises(SpecError):
            create_record(self.root, "EXP-001", "plan", None, "researcher", "overwrite")
        self.assertEqual((self.workspace / "EXPERIMENTS.md").read_bytes(), before)

    def test_plan_must_be_complete_before_starting_run(self):
        with self.assertRaisesRegex(SpecError, "补齐计划"):
            create_record(self.root, "EXP-001", "run", "RUN-001", "researcher")
        self.assertFalse((self.plan.parent / "runs").exists())

    def test_retries_have_unique_ids_and_keep_failed_runs(self):
        first, _ = self.completed_run(state="failed")
        before = first.read_bytes()
        with self.assertRaises(SpecError):
            create_record(self.root, "EXP-001", "run", "RUN-001", "researcher")
        second, _ = self.completed_run("RUN-002")
        self.assertEqual(first.read_bytes(), before)
        self.assertTrue(second.exists())
        conclusion = self.reviewed_conclusion()
        self.assertIn("RUN-001", conclusion.read_text())
        self.assertIn("RUN-002", conclusion.read_text())
        self.assertEqual(self.codes(), set())

    def test_plan_edits_do_not_rewrite_previous_run_snapshot(self):
        path, _ = self.completed_run()
        data, _ = read_record(path)
        snapshot = self.workspace / data["plan_snapshot"]
        before = snapshot.read_bytes()
        self.update(self.plan, sections={"Design": "后续设计改变"})
        self.assertEqual(snapshot.read_bytes(), before)
        self.assertNotIn("invalid_plan_snapshot", self.codes())
        snapshot.write_text("tampered", encoding="utf-8")
        self.assertIn("invalid_plan_snapshot", self.codes())

    def test_conclusion_cannot_be_created_while_run_is_running(self):
        path, _ = self.completed_run()
        self.update(path, {"status": "running"})
        with self.assertRaisesRegex(SpecError, "未结束"):
            create_record(self.root, "EXP-001", "conclusion", "CON-001", "lead")

    def test_negative_result_can_finish_but_requires_review(self):
        self.completed_run()
        self.update(self.plan, {"status": "completed"})
        self.assertIn("missing_experiment_conclusion", self.codes())
        self.reviewed_conclusion()
        self.assertEqual(self.codes(), set())

    def test_run_mutation_invalidates_reviewed_conclusion(self):
        run, _ = self.completed_run()
        self.reviewed_conclusion()
        self.update(run, sections={"Metrics": "更正指标"})
        self.assertIn("stale_conclusion_evidence", self.codes())

    def test_corrected_runs_keep_history_and_valid_replacements_close_drift(self):
        run, _ = self.completed_run()
        original = run.read_bytes()
        self.reviewed_conclusion()
        record_work(self.root, "experiments/EXP-001/runs/RUN-001.md", "researcher", "correction", "指标需纠错")
        self.update(run, sections={"Metrics": "更正后的实测值"})
        self.assertIn("stale_conclusion_evidence", self.codes())
        self.reviewed_conclusion("CON-002", "CON-001")
        self.assertEqual(self.codes(), set())
        snapshots = list((self.plan.parent / "evidence/RUN-001").glob("*.md"))
        self.assertIn(original, [path.read_bytes() for path in snapshots])
        self.update(run, sections={"Metrics": "第二次纠错"})
        self.reviewed_conclusion("CON-003", "CON-002")
        self.assertEqual(self.codes(), set())
        with self.assertRaises(SpecError):
            record_work(self.root, snapshots[0].relative_to(self.workspace.resolve()).as_posix(), "researcher", "edit", "改历史")
        snapshots[0].write_text("tampered", encoding="utf-8")
        self.assertIn("invalid_run_snapshot", self.codes())

    def test_conclusion_creation_respects_run_writer_lock(self):
        run, _ = self.completed_run()
        with record_lock(self.workspace, run):
            with self.assertRaisesRegex(SpecError, "locked"):
                create_record(self.root, "EXP-001", "conclusion", "CON-001", "lead")
        self.assertFalse((self.plan.parent / "conclusions/CON-001.md").exists())
        self.assertFalse((self.plan.parent / "evidence").exists())

    def test_review_template_is_not_evidence(self):
        self.completed_run()
        conclusion = self.reviewed_conclusion()
        data, _ = read_record(conclusion)
        report = self.root / data["review_evidence"]
        self.update(report, sections={"Findings": "unknown", "Assessment": "unknown"})
        self.assertIn("invalid_experiment_review", self.codes())
        self.update(conclusion, sections={"Review": "unknown"})
        self.assertIn("incomplete_conclusion", self.codes())

    def test_malformed_artifact_uri_is_a_finding_not_exception(self):
        run, artifact = self.completed_run()
        self.update(run, sections={"Artifacts": f"| Path | SHA256 | Purpose |\n|---|---|---|\n| https://[broken/log | {digest_file(artifact)} | 日志 |"})
        self.assertIn("invalid_artifact_uri", self.codes())

    def test_conclusion_mutation_invalidates_review_report(self):
        self.completed_run()
        conclusion = self.reviewed_conclusion()
        self.update(conclusion, sections={"Analysis": "改变结论"})
        self.assertIn("invalid_experiment_review", self.codes())

    def test_new_run_requires_new_complete_conclusion(self):
        self.completed_run()
        self.reviewed_conclusion()
        self.completed_run("RUN-002", "failed")
        self.update(self.plan, {"status": "completed"})
        self.assertIn("missing_experiment_conclusion", self.codes())
        self.reviewed_conclusion("CON-002")
        self.assertNotIn("missing_experiment_conclusion", self.codes())

    def test_local_artifact_hash_is_verified_only_on_request(self):
        _, artifact = self.completed_run()
        artifact.write_text("changed", encoding="utf-8")
        self.assertNotIn("invalid_run_artifact", self.codes())
        self.assertIn("invalid_run_artifact", self.codes(verify=True))

    def test_failed_run_without_artifacts_is_retained_honestly(self):
        path, _ = self.completed_run(state="failed")
        self.update(path, {"artifacts_status": "unavailable"}, {"Artifacts": "", "Metrics": "not_measured"})
        _, findings = inspect_experiments(self.workspace)
        self.assertEqual({f["severity"] for f in findings}, {"P3"})

    def test_invalid_exit_time_and_self_review_are_detected(self):
        path, _ = self.completed_run()
        conclusion = self.reviewed_conclusion()
        self.update(path, {"exit_code": "1", "ended": "2026-10-01T00:00:00Z"})
        self.update(conclusion, {"reviewer": "lead"})
        self.assertTrue({"invalid_run_exit", "invalid_run_time", "invalid_experiment_reviewer"} <= self.codes())

    def test_archive_does_not_hide_incomplete_runs(self):
        path, _ = self.completed_run()
        self.update(path, {"status": "running"})
        self.update(self.plan, {"status": "cancelled", "archived": "true"})
        self.assertTrue({"unfinished_experiment_run", "invalid_experiment_archive", "incomplete_experiment_archive"} <= self.codes())

    def test_cancelling_unstarted_run_requires_no_fabricated_execution(self):
        self.ready_plan()
        path = create_record(self.root, "EXP-001", "run", "RUN-001", "researcher")
        self.update(path, {"status": "cancelled", "ended": "2026-10-02T00:01:00Z"},
                    {"Observations": "未启动，预算已用完"})
        self.assertEqual(self.codes(), set())
        self.update(path, {"started": "2026-10-02T00:00:00Z"})
        self.assertIn("invalid_run_cancellation", self.codes())

    def test_paths_and_concurrent_plan_writes_are_rejected(self):
        self.ready_plan()
        with self.assertRaises(SpecError):
            create_record(self.root, "../out", "plan", None, "researcher", "escape")
        with record_lock(self.workspace, self.plan):
            with self.assertRaisesRegex(SpecError, "locked"):
                create_record(self.root, "EXP-001", "run", "RUN-001", "researcher")

    def test_deployed_ci_and_creation_runtime_are_complete(self):
        install_ci(self.root)
        init_workspace(self.root, "minimal", ["scripts"])
        scripts = self.workspace / "scripts"
        self.ready_plan()
        result = subprocess.run([sys.executable, str(scripts / "create_experiment.py"), str(self.root),
                                 "EXP-001", "--kind", "run", "--record-id", "RUN-001", "--owner", "researcher", "--json"],
                                text=True, capture_output=True, check=True)
        self.assertTrue(json.loads(result.stdout)["ok"])
        result = subprocess.run([sys.executable, str(scripts / "check_vibe_spec.py"), str(self.root), "--json"],
                                text=True, capture_output=True)
        self.assertIn("findings", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
