#!/usr/bin/env python3
"""检查目标项目的 .vibe-spec 结构、状态和常见治理缺口。"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_CORE_FILES = [
    "PROJECT_SPEC.md",
    "AGENT_GUIDE.md",
    "STYLE_GUIDE.md",
    "LIFECYCLE.md",
    "SPEC_INDEX.md",
    "MODULES.md",
]

MODULE_REQUIRED_FILES = {
    "memory": ["DECISIONS.md", "FILE_MAP.md"],
    "testing": ["TESTING_GUIDE.md"],
    "data": ["DATA_GUIDE.md"],
    "experiments": ["EXPERIMENTS.md"],
    "security": ["SECURITY_GUIDE.md"],
    "release": ["RELEASE_GUIDE.md"],
    "migration": ["MIGRATION_GUIDE.md"],
    "environment": ["ENVIRONMENT_GUIDE.md"],
    "observability": ["OBSERVABILITY_GUIDE.md"],
    "contracts": ["CONTRACTS.md"],
}

VALID_STATES = {
    "idea",
    "draft",
    "ready_for_review",
    "approved",
    "in_progress",
    "implemented",
    "verification_failed",
    "verified",
    "reviewed",
    "active",
    "needs_update",
    "needs_sync",
    "needs_changes",
    "superseded",
    "deprecated",
    "archived",
}

IMPLEMENTED_STATES = {"implemented", "verified", "reviewed", "active"}
VERIFIED_STATES = {"verified", "reviewed", "active"}
REVIEWED_STATES = {"reviewed", "active"}
ACTIVE_LIKE_STATES = {"active", "needs_update", "needs_sync"}


@dataclass
class Finding:
    severity: str
    code: str
    location: str
    message: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def parse_enabled_modules(modules_file: Path) -> set[str]:
    if not modules_file.exists():
        return set()
    enabled: set[str] = set()
    for line in read_text(modules_file).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        module, value = cells[0], cells[1].lower()
        if module in {"模块", "---"}:
            continue
        if value in {"yes", "enabled", "true", "启用"}:
            enabled.add(module)
    return enabled


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter = text[3:end].strip()
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def has_meaningful_section(text: str, heading: str) -> bool:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return False
    next_heading = re.search(r"^## ", text[match.end() :], re.MULTILINE)
    section = text[match.end() : match.end() + next_heading.start()] if next_heading else text[match.end() :]
    stripped = section.strip()
    return bool(stripped and stripped not in {"TBD", "尚未实现。", "尚未审核。", "No implementation yet.", "No review yet."})


def check_workspace(workspace: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not workspace.exists():
        return [
            Finding(
                "P0",
                "missing_workspace",
                str(workspace),
                "缺少 .vibe-spec 工作区。先运行 init_vibe_spec.py。",
            )
        ]

    for name in REQUIRED_CORE_FILES:
        if not (workspace / name).exists():
            findings.append(Finding("P1", "missing_core_file", name, "缺少 core 文件。"))

    enabled_modules = parse_enabled_modules(workspace / "MODULES.md")
    if not enabled_modules:
        findings.append(Finding("P2", "unknown_modules", "MODULES.md", "无法识别已启用模块。"))

    for module in enabled_modules:
        for name in MODULE_REQUIRED_FILES.get(module, []):
            if not (workspace / name).exists():
                findings.append(
                    Finding("P1", "missing_module_file", name, f"模块 `{module}` 已启用，但缺少文件。")
                )

    specs_dir = workspace / "specs"
    if not specs_dir.exists():
        findings.append(Finding("P1", "missing_specs_dir", "specs/", "缺少 specs 目录。"))
    else:
        spec_files = sorted(specs_dir.glob("*.md"))
        if not spec_files:
            findings.append(Finding("P3", "no_specs", "specs/", "当前没有任何 spec 文件。"))
        for spec_file in spec_files:
            findings.extend(check_spec_file(spec_file))

    if "review" in enabled_modules:
        reports_dir = workspace / "reports"
        if not reports_dir.exists():
            findings.append(Finding("P2", "missing_reports_dir", "reports/", "review 模块已启用，但缺少 reports 目录。"))

    if "scripts" in enabled_modules and not (workspace / "scripts").exists():
        findings.append(Finding("P2", "missing_scripts_dir", "scripts/", "scripts 模块已启用，但缺少 scripts 目录。"))

    return findings


def check_spec_file(spec_file: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = read_text(spec_file)
    frontmatter = parse_frontmatter(text)
    status = frontmatter.get("status", "")
    spec_id = frontmatter.get("spec_id", spec_file.stem)
    location = str(spec_file)

    if not frontmatter:
        findings.append(Finding("P2", "missing_frontmatter", location, "spec 缺少 frontmatter。"))
    if not spec_id:
        findings.append(Finding("P2", "missing_spec_id", location, "spec 缺少 spec_id。"))
    if not status:
        findings.append(Finding("P2", "missing_status", location, "spec 缺少 status。"))
    elif status not in VALID_STATES:
        findings.append(Finding("P1", "invalid_status", location, f"未知 status `{status}`。"))

    required_sections = [
        "Summary",
        "Context",
        "Goals",
        "Non-Goals",
        "Requirements",
        "Acceptance Criteria",
        "Verification Plan",
        "Lifecycle Log",
    ]
    for heading in required_sections:
        if f"## {heading}" not in text:
            findings.append(Finding("P2", "missing_section", location, f"缺少章节 `## {heading}`。"))

    if status in IMPLEMENTED_STATES and not has_meaningful_section(text, "Implementation Notes"):
        findings.append(Finding("P1", "missing_implementation_notes", location, "已实现状态缺少有效 Implementation Notes。"))
    if status in VERIFIED_STATES and not has_meaningful_section(text, "Verification Plan"):
        findings.append(Finding("P1", "missing_verification_evidence", location, "已验证状态缺少有效验证记录。"))
    if status in REVIEWED_STATES and not has_meaningful_section(text, "Review Notes"):
        findings.append(Finding("P1", "missing_review_notes", location, "已 review/active 状态缺少有效 Review Notes。"))
    if status in ACTIVE_LIKE_STATES and "TBD" in text:
        findings.append(Finding("P2", "active_has_tbd", location, "active/needs_* spec 仍包含 TBD。"))

    return findings


def format_findings(findings: list[Finding]) -> str:
    if not findings:
        return "vibe-spec check: PASS\n"

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    lines = ["vibe-spec check: FINDINGS", ""]
    for finding in sorted(findings, key=lambda item: (order.get(item.severity, 9), item.code, item.location)):
        lines.append(f"- {finding.severity} [{finding.code}] {finding.location}: {finding.message}")
    lines.append("")
    return "\n".join(lines)


def should_fail(findings: list[Finding], strict: bool) -> bool:
    failing = {"P0", "P1"}
    if strict:
        failing.add("P2")
    return any(finding.severity in failing for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查目标项目的 .vibe-spec。")
    parser.add_argument("target", nargs="?", default=".", help="目标项目路径，默认当前目录。")
    parser.add_argument("--strict", action="store_true", help="P2 也作为失败。")
    parser.add_argument("--quiet", action="store_true", help="无问题时不输出。")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    workspace = target / ".vibe-spec"
    findings = check_workspace(workspace)

    if findings or not args.quiet:
        print(format_findings(findings), end="")

    return 1 if should_fail(findings, args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
