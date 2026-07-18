from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_ROOT / "SKILL.md"
OPENAI_YAML = SKILL_ROOT / "agents" / "openai.yaml"


class SkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_skill_frontmatter_and_size_are_cross_agent_friendly(self) -> None:
        self.assertTrue(self.text.startswith("---\n"))
        frontmatter = self.text.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: vibe-spec$")
        self.assertRegex(frontmatter, r"(?m)^description: .*(跨 Agent|跨工具)")
        self.assertNotRegex(frontmatter, r"(?m)^argument-hint:")
        self.assertRegex(frontmatter, r"(?m)^metadata:\n\s+argument-hint:")
        self.assertRegex(frontmatter, r"(?m)^allowed-tools:")
        self.assertLess(len(self.text.splitlines()), 500)

    def test_skill_routes_context_and_automation_commands(self) -> None:
        for command in (
            "init",
            "context",
            "handoff",
            "roadmap",
            "spec",
            "promote",
            "review",
            "status",
            "check",
            "sync",
            "retire",
        ):
            self.assertRegex(self.text, rf"`{command}(?:\s|`)" )
        self.assertIn("references/automation.md", self.text)

    def test_skill_defines_start_and_end_context_protocol(self) -> None:
        self.assertIn("HANDOFF.md", self.text)
        self.assertIn("ROADMAP.md", self.text)
        self.assertIn("FILE_MAP.md", self.text)
        self.assertRegex(self.text, r"开始工作.*HANDOFF", re.DOTALL)
        self.assertRegex(self.text, r"暂停、完成或切换 Agent.*HANDOFF", re.DOTALL)

    def test_skill_keeps_agent_judgment_and_review_fallback(self) -> None:
        self.assertIn("Agent-first", self.text)
        self.assertIn("subagent", self.text)
        self.assertIn("不支持 subagent", self.text)
        self.assertIn("不能替代", self.text)

    def test_openai_metadata_is_present_and_invokes_skill(self) -> None:
        self.assertTrue(OPENAI_YAML.exists())
        metadata = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn('display_name: "Vibe Spec"', metadata)
        self.assertRegex(metadata, r'short_description: ".{25,64}"')
        self.assertIn("$vibe-spec", metadata)


if __name__ == "__main__":
    unittest.main()
