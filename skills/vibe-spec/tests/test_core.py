from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vibe_spec_core import (  # noqa: E402
    CommandResult,
    SpecError,
    append_lifecycle,
    emit_result,
    find_spec,
    load_spec,
    rebuild_spec_index,
    replace_section,
    write_spec,
)


SPEC_TEXT = """---
spec_id: login-flow
status: draft
parent: project
extends: [base-auth, audit-policy]
supersedes: []
created: 2026-07-18
updated: 2026-07-18
owner_agent: codex
---

# Spec: Login Flow

## Summary

Initial summary.

## Lifecycle Log

- 2026-07-18: created as `draft`.
"""


class CoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.workspace = self.root / ".vibe-spec"
        (self.workspace / "specs").mkdir(parents=True)
        (self.workspace / "SPEC_INDEX.md").write_text("# Spec 索引\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_fixture(self, name: str = "2026-07-18-login-flow.md") -> Path:
        path = self.workspace / "specs" / name
        path.write_text(SPEC_TEXT, encoding="utf-8")
        return path

    def test_load_and_write_round_trip_constrained_frontmatter(self) -> None:
        path = self.write_fixture()

        spec = load_spec(path)

        self.assertEqual(spec.spec_id, "login-flow")
        self.assertEqual(spec.status, "draft")
        self.assertEqual(spec.metadata["extends"], ["base-auth", "audit-policy"])
        spec.metadata["status"] = "ready_for_review"
        write_spec(spec)
        reloaded = load_spec(path)
        self.assertEqual(reloaded.status, "ready_for_review")
        self.assertEqual(reloaded.metadata["extends"], ["base-auth", "audit-policy"])

    def test_replace_section_preserves_other_sections(self) -> None:
        updated = replace_section(SPEC_TEXT, "Summary", "Revised summary.")

        self.assertIn("## Summary\n\nRevised summary.", updated)
        self.assertIn("## Lifecycle Log", updated)
        self.assertNotIn("Initial summary.", updated)

    def test_append_lifecycle_adds_a_single_entry(self) -> None:
        updated = append_lifecycle(
            SPEC_TEXT,
            "2026-07-18",
            "draft",
            "ready_for_review",
            "spec complete",
            "acceptance criteria checked",
        )

        self.assertIn("`draft` -> `ready_for_review`", updated)
        self.assertIn("spec complete", updated)
        self.assertIn("acceptance criteria checked", updated)

    def test_find_spec_rejects_duplicate_ids(self) -> None:
        self.write_fixture()
        self.write_fixture("2026-07-18-duplicate-name.md")

        with self.assertRaisesRegex(SpecError, "duplicate spec_id"):
            find_spec(self.root, "login-flow")

    def test_rebuild_index_lists_specs_in_stable_order(self) -> None:
        first = self.write_fixture()
        second_text = SPEC_TEXT.replace("login-flow", "account-settings").replace("status: draft", "status: approved")
        (self.workspace / "specs" / "2026-07-18-account-settings.md").write_text(second_text, encoding="utf-8")

        rebuild_spec_index(self.root)

        index = (self.workspace / "SPEC_INDEX.md").read_text(encoding="utf-8")
        self.assertLess(index.index("account-settings"), index.index("login-flow"))
        self.assertIn("| approved |", index)
        self.assertIn(f"`specs/{first.name}`", index)

    def test_json_result_uses_stable_contract(self) -> None:
        result = CommandResult(
            ok=True,
            command="test",
            changes=["one"],
            findings=[],
            next_actions=["two"],
        )
        output = io.StringIO()

        with redirect_stdout(output):
            emit_result(result, as_json=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(
            set(payload),
            {"ok", "command", "changes", "findings", "next_actions"},
        )
        self.assertEqual(payload["command"], "test")


if __name__ == "__main__":
    unittest.main()
