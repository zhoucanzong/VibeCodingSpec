from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from update_handoff import update_handoff
from vibe_spec_core import SpecError
from work_records import append_progress, record_lock, record_work


class WorkRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / ".vibe-spec"
        self.workspace.mkdir()
        self.handoff = self.workspace / "HANDOFF.md"
        self.handoff.write_text("# Handoff\n\n## Context Links\n\n[Project](PROJECT_SPEC.md)\n", encoding="utf-8")
        self.record = self.workspace / "collaboration/tasks/task.md"
        self.record.parent.mkdir(parents=True)
        self.original = "---\ntask_id: stable\nstatus: running\n---\n# Task\n\n## Progress\n\n- prior entry  \n\n## Result\n\nnot accepted\n"
        self.record.write_text(self.original, encoding="utf-8")

    def update(self, state="running"):
        return update_handoff(self.root, "goal", state, "review", ["project"], [], [], [])

    def append(self, **kwargs):
        arguments = dict(target=self.root, record="collaboration/tasks/task.md", actor="agent",
                         event="checkpoint", summary="tests passed")
        arguments.update(kwargs)
        return record_work(**arguments)

    def histories(self, kind):
        return sorted((self.workspace / "history" / kind).glob("*.md"))

    def assert_unlocked(self):
        self.assertFalse(list((self.workspace / ".locks").glob("*.lock")))

    def fail_replace(self, destination):
        original_replace = Path.replace

        def replace(source, target):
            if Path(target) == destination:
                raise OSError("injected replacement failure")
            return original_replace(source, target)

        return patch.object(Path, "replace", replace)

    def test_handoff_repeated_update_is_noop(self):
        self.assertEqual(self.update(), self.handoff)
        first = self.handoff.read_bytes()
        mtime = self.handoff.stat().st_mtime_ns
        self.update()
        self.assertEqual(self.handoff.read_bytes(), first)
        self.assertEqual(self.handoff.stat().st_mtime_ns, mtime)
        self.assertEqual(len(self.histories("handoffs")), 1)
        self.assert_unlocked()

    def test_handoff_equal_content_preserves_existing_formatting(self):
        self.update()
        text = self.handoff.read_text().replace("## Current Goal\n\ngoal\n", "## Current Goal\n\n  goal  \n\n")
        self.handoff.write_text(text)
        self.update()
        self.assertEqual(self.handoff.read_text(), text)
        self.assertEqual(len(self.histories("handoffs")), 1)

    def test_handoff_history_is_complete_and_continuous(self):
        previous = []
        with patch("work_records.utc_now", return_value="2026-10-02T00:00:00.000000Z"):
            for state in ("running", "blocked", "done"):
                previous.append(self.handoff.read_text())
                self.update(state)
        history = self.histories("handoffs")
        self.assertEqual(len(history), 3)
        self.assertCountEqual([path.read_text() for path in history], previous)
        self.assertTrue(all(path.name.startswith("20261002T000000.000000Z-") for path in history))
        self.assertIn("[Project](PROJECT_SPEC.md)", self.handoff.read_text())

    def test_snapshot_preserves_complete_crlf_original(self):
        original = b"# Handoff\r\n\r\nCustom content\r\n"
        self.handoff.write_bytes(original)
        self.update()
        self.assertEqual(self.histories("handoffs")[0].read_bytes(), original)

    def test_handoff_failed_replace_rolls_back_history(self):
        original = self.handoff.read_bytes()
        with self.fail_replace(self.handoff), self.assertRaises(OSError):
            self.update()
        self.assertEqual(self.handoff.read_bytes(), original)
        self.assertEqual(self.histories("handoffs"), [])
        self.assert_unlocked()

    def test_handoff_invalid_spec_does_not_create_history(self):
        original = self.handoff.read_bytes()
        with self.assertRaises(SpecError):
            update_handoff(self.root, "goal", "running", "review", ["absent"], [], [], [])
        self.assertEqual(self.handoff.read_bytes(), original)
        self.assertEqual(self.histories("handoffs"), [])

    def test_append_does_not_rewrite_old_content_and_links_both_ways(self):
        record, first = self.append(evidence=["command -> PASS (exit 0)", "output/log.txt"], next_action="review")
        first_bytes = first.read_bytes()
        previous_entry = next(line for line in record.read_text().splitlines() if first.stem in line)
        _, second = self.append(summary="correction: one test skipped")
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), first_bytes)
        text = record.read_text()
        self.assertIn(self.original.split("## Result")[0], text)
        self.assertTrue(text.endswith("## Result\n\nnot accepted\n"))
        self.assertIn(previous_entry, text)
        self.assertLess(text.index(first.stem), text.index(second.stem))
        self.assertLess(text.index(second.stem), text.index("## Result"))
        for value in ("../../collaboration/tasks/task.md", "command -> PASS (exit 0)", "output/log.txt", "review"):
            self.assertIn(value, first.read_text())
        self.assert_unlocked()

    def test_duplicate_event_is_a_new_append_not_an_overwrite(self):
        self.append()
        self.append()
        self.assertEqual(len(self.histories("events")), 2)
        self.assertEqual(self.record.read_text().count("tests passed"), 2)

    def test_progress_is_added_when_missing_and_ignores_fenced_headings(self):
        original = "# Record\n\n```md\n## Progress\n```\n"
        text = append_progress(original, "- new entry")
        self.assertTrue(text.startswith(original))
        self.assertTrue(text.endswith("## Progress\n\n- new entry\n"))
        original = "## Progress\n\n```md\n## fake\n```\n\n## Result\n\nold\n"
        text = append_progress(original, "- new entry")
        self.assertIn("```md\n## fake\n```", text)
        self.assertLess(text.index("- new entry"), text.index("## Result"))

    def test_record_replace_failure_leaves_original_and_no_event(self):
        with self.fail_replace(self.record), self.assertRaises(OSError):
            self.append()
        self.assertEqual(self.record.read_text(), self.original)
        self.assertEqual(self.histories("events"), [])
        self.assert_unlocked()

    def test_prewrite_failure_leaves_original_and_no_event(self):
        import vibe_spec_core
        mkstemp = vibe_spec_core.tempfile.mkstemp
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected staging failure")
            return mkstemp(*args, **kwargs)

        with patch("vibe_spec_core.tempfile.mkstemp", side_effect=fail_second), self.assertRaises(OSError):
            self.append()
        self.assertEqual(self.record.read_text(), self.original)
        self.assertEqual(self.histories("events"), [])
        self.assertFalse(list((self.workspace / "history/events").iterdir()))
        self.assert_unlocked()

    def test_uuid_collision_never_overwrites_history(self):
        with patch("work_records.uuid.uuid4", return_value=uuid.UUID(int=1)):
            _, history = self.append()
            history_bytes, record_bytes = history.read_bytes(), self.record.read_bytes()
            with self.assertRaises(SpecError):
                self.append(summary="must fail")
        self.assertEqual(history.read_bytes(), history_bytes)
        self.assertEqual(self.record.read_bytes(), record_bytes)
        self.assert_unlocked()

    def test_rejects_unsafe_or_nonrecord_paths(self):
        for name in ("history/events/old.md", "templates/TASK.md", "assets/templates/TASK.md"):
            path = self.workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("immutable")
        for name in ("", "../outside.md", "tasks/../../outside.md", str(self.record),
                     "history/events/old.md", "templates/TASK.md", "assets/templates/TASK.md",
                     "missing.md", "collaboration/tasks", "a.txt", "C:\\outside.md", "bad\x00.md"):
            with self.subTest(name=name), self.assertRaises(SpecError):
                self.append(record=name)
        self.assertEqual(self.histories("events")[0].read_text(), "immutable")
        self.assertEqual(self.record.read_text(), self.original)

    def test_rejects_external_file_and_directory_symlinks(self):
        outside = self.root / "outside.md"
        outside.write_text("outside")
        (self.workspace / "alias.md").symlink_to(outside)
        (self.workspace / "alias-dir").symlink_to(self.root, target_is_directory=True)
        for name in ("alias.md", "alias-dir/outside.md"):
            with self.subTest(name=name), self.assertRaises(SpecError):
                self.append(record=name)
        self.assertEqual(outside.read_text(), "outside")

    def test_rejects_internal_alias_to_history(self):
        history = self.workspace / "history/events/old.md"
        history.parent.mkdir(parents=True)
        history.write_text("immutable")
        (self.workspace / "alias.md").symlink_to(history)
        with self.assertRaises(SpecError):
            self.append(record="alias.md")
        self.assertEqual(history.read_text(), "immutable")

    def test_rejects_symlinked_history_storage(self):
        (self.workspace / "history").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SpecError):
            self.append()
        with self.assertRaises(SpecError):
            self.update()
        self.assertEqual(self.record.read_text(), self.original)
        self.assertFalse((self.root / "events").exists())

    def test_handoff_cannot_alias_immutable_history(self):
        history = self.workspace / "history/handoffs/old.md"
        history.parent.mkdir(parents=True)
        history.write_text("immutable")
        self.handoff.unlink()
        self.handoff.symlink_to(history)
        with self.assertRaises(SpecError):
            self.update()
        self.assertEqual(history.read_text(), "immutable")

    def test_handoff_cannot_alias_external_file(self):
        outside = self.root / "outside.md"
        outside.write_text("outside")
        self.handoff.unlink()
        self.handoff.symlink_to(outside)
        with self.assertRaises(SpecError):
            self.update()
        self.assertEqual(outside.read_text(), "outside")

    def test_lock_directory_cannot_be_a_symlink(self):
        (self.workspace / ".locks").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SpecError):
            with record_lock(self.workspace, self.record):
                self.fail("symlinked lock directory accepted")
        self.assertFalse(list(self.root.glob("*.lock")))

    def test_lock_accepts_nonexistent_record_and_normalizes_paths(self):
        path = self.workspace / "experiments/new/PLAN.md"
        with record_lock(self.workspace, path):
            self.assertFalse(path.exists())
            with self.assertRaises(SpecError):
                with record_lock(self.workspace, Path("experiments/new/../new/PLAN.md")):
                    self.fail("lock must reject normalized duplicate")
            with record_lock(self.workspace, Path("experiments/other/PLAN.md")):
                pass
        self.assert_unlocked()

    def test_lock_requires_workspace_and_containment(self):
        for workspace, record in ((self.root / "missing", Path("new.md")),
                                  (self.workspace, self.root / "outside.md"),
                                  (self.workspace, Path("../outside.md")),
                                  (self.workspace, self.workspace)):
            with self.subTest(record=record), self.assertRaises((SpecError, OSError)):
                with record_lock(workspace, record):
                    self.fail("invalid lock accepted")
        self.assertFalse((self.root / "missing").exists())

    def test_lock_rejects_external_symlink_even_for_missing_leaf(self):
        (self.workspace / "external").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SpecError):
            with record_lock(self.workspace, Path("external/new/PLAN.md")):
                self.fail("escaped lock accepted")

    def test_lock_internal_alias_uses_same_key(self):
        alias = self.workspace / "alias.md"
        alias.symlink_to(self.record)
        with record_lock(self.workspace, self.record), self.assertRaises(SpecError):
            with record_lock(self.workspace, alias):
                self.fail("alias lock accepted")

    def test_lock_released_on_failure(self):
        with self.assertRaises(RuntimeError):
            with record_lock(self.workspace, self.record):
                raise RuntimeError("failure")
        self.assert_unlocked()
        with record_lock(self.workspace, self.record):
            pass

    def test_record_and_handoff_share_lock_protocol(self):
        with record_lock(self.workspace, self.handoff):
            with self.assertRaises(SpecError):
                self.update()
            with self.assertRaises(SpecError):
                self.append(record="HANDOFF.md")
        self.assertFalse((self.workspace / "history").exists())

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "record_work.py"), str(self.root),
                               *args, "--json"], text=True, capture_output=True, timeout=10)

    def test_another_process_fails_fast_on_same_record(self):
        with record_lock(self.workspace, self.record):
            result = self.cli("collaboration/tasks/task.md", "--actor", "other", "--event", "update",
                              "--summary", "must not append")
            self.assertNotEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)["ok"])
            self.assertIn("locked", result.stdout)
        self.assertEqual(self.record.read_text(), self.original)
        self.assertEqual(self.histories("events"), [])
        self.assert_unlocked()

    def test_cli_uses_command_result_and_repeated_evidence(self):
        result = self.cli("collaboration/tasks/task.md", "--actor", "agent", "--event", "check",
                          "--summary", "passed", "--evidence", "first", "--evidence", "second",
                          "--next-action", "review")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"ok", "command", "changes", "findings", "next_actions"})
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "record-work")
        self.assertEqual(len(payload["changes"]), 2)
        history = self.histories("events")[0].read_text()
        self.assertIn("first\n\nsecond", history)

    def test_empty_fields_rejected_without_writes(self):
        for field in ("actor", "event", "summary"):
            with self.subTest(field=field), self.assertRaises(SpecError):
                self.append(**{field: "  "})
        self.assertFalse((self.workspace / "history").exists())


if __name__ == "__main__":
    unittest.main()
