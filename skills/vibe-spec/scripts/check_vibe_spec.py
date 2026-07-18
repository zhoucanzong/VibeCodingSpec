#!/usr/bin/env python3
"""检查 .vibe-spec 结构、索引、引用、状态证据和交接上下文。"""

from __future__ import annotations

import argparse
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    VALID_STATES,
    emit_result,
    meaningful,
    parse_frontmatter,
    section_content,
)


REQUIRED_CORE_FILES = [
    "PROJECT_SPEC.md",
    "AGENT_GUIDE.md",
    "STYLE_GUIDE.md",
    "LIFECYCLE.md",
    "SPEC_INDEX.md",
    "MODULES.md",
    "HANDOFF.md",
    "ROADMAP.md",
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


@dataclass
class SpecRecord:
    path: Path
    metadata: dict[str, object]
    text: str

    @property
    def spec_id(self) -> str:
        return str(self.metadata.get("spec_id", ""))

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", ""))


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
        if module not in {"模块", "---"} and value in {"yes", "enabled", "true", "启用"}:
            enabled.add(module)
    return enabled


def parse_specs(specs_dir: Path) -> tuple[list[SpecRecord], list[Finding]]:
    records: list[SpecRecord] = []
    findings: list[Finding] = []
    for path in sorted(specs_dir.glob("*.md")):
        text = read_text(path)
        try:
            metadata, _ = parse_frontmatter(text)
        except RuntimeError as exc:
            findings.append(Finding("P2", "missing_frontmatter", str(path), str(exc)))
            metadata = {}
        records.append(SpecRecord(path, metadata, text))
    return records, findings


def index_entries(index_path: Path) -> dict[str, str]:
    if not index_path.exists():
        return {}
    result: dict[str, str] = {}
    for line in read_text(index_path).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[0] not in {"Spec ID", "---", "project"}:
            result[cells[0]] = cells[2]
    return result


def list_value(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value or value == "[]":
        return []
    return [item.strip() for item in str(value).strip("[]").split(",") if item.strip()]


def check_spec(record: SpecRecord) -> list[Finding]:
    findings: list[Finding] = []
    location = str(record.path)
    if not record.spec_id:
        findings.append(Finding("P2", "missing_spec_id", location, "spec 缺少 spec_id。"))
    if not record.status:
        findings.append(Finding("P2", "missing_status", location, "spec 缺少 status。"))
    elif record.status not in VALID_STATES:
        findings.append(Finding("P1", "invalid_status", location, f"未知 status `{record.status}`。"))

    for heading in (
        "Summary",
        "Context",
        "Goals",
        "Non-Goals",
        "Requirements",
        "Acceptance Criteria",
        "Verification Plan",
        "Lifecycle Log",
    ):
        if section_content(record.text, heading) is None:
            findings.append(Finding("P2", "missing_section", location, f"缺少章节 `## {heading}`。"))
    if record.status in IMPLEMENTED_STATES and not meaningful(section_content(record.text, "Implementation Notes")):
        findings.append(Finding("P1", "missing_implementation_notes", location, "已实现状态缺少有效实现记录。"))
    verification = section_content(record.text, "Verification Plan") or ""
    if record.status in VERIFIED_STATES and not re.search(r"(?i)(`[^`]+`.*(pass|通过|exit\s*0)|结果\s*[:：].*(pass|通过|成功))", verification):
        findings.append(Finding("P1", "missing_verification_evidence", location, "已验证状态缺少通过证据。"))
    review = section_content(record.text, "Review Notes") or ""
    if record.status in REVIEWED_STATES and not re.search(r"(?i)(pass|approved|通过|无阻塞)", review):
        findings.append(Finding("P1", "missing_review_notes", location, "已审核状态缺少通过记录。"))
    if record.status in ACTIVE_LIKE_STATES and "TBD" in record.text:
        findings.append(Finding("P2", "active_has_tbd", location, "active/needs_* spec 仍包含 TBD。"))
    if record.status not in {"", "idea", "draft"}:
        lifecycle = section_content(record.text, "Lifecycle Log") or ""
        target_state = re.escape(record.status)
        evidence = re.search(rf"->\s*`{target_state}`", lifecycle) or re.search(
            rf"\|[^|\n]*\|\s*{target_state}\s*\|", lifecycle
        )
        if not evidence:
            findings.append(
                Finding("P1", "missing_lifecycle_evidence", location, f"状态 `{record.status}` 没有对应生命周期记录。")
            )
    return findings


def check_handoff(workspace: Path) -> list[Finding]:
    path = workspace / "HANDOFF.md"
    if not path.exists():
        return []
    text = read_text(path)
    incomplete = []
    for heading in ("Current Goal", "Working State", "Next Action"):
        content = section_content(text, heading)
        if not meaningful(content) or (content and "unknown" in content.lower()):
            incomplete.append(heading)
    if not incomplete:
        return []
    return [
        Finding(
            "P2",
            "incomplete_handoff",
            "HANDOFF.md",
            "交接入口尚未补齐：" + ", ".join(incomplete),
        )
    ]


def check_workspace(workspace: Path) -> list[Finding]:
    if not workspace.exists():
        return [Finding("P0", "missing_workspace", str(workspace), "缺少 .vibe-spec 工作区。")]
    findings: list[Finding] = []
    for name in REQUIRED_CORE_FILES:
        if not (workspace / name).exists():
            findings.append(Finding("P1", "missing_core_file", name, "缺少 core 文件。"))

    enabled = parse_enabled_modules(workspace / "MODULES.md")
    if not enabled:
        findings.append(Finding("P2", "unknown_modules", "MODULES.md", "无法识别已启用模块。"))
    for module in enabled:
        for name in MODULE_REQUIRED_FILES.get(module, []):
            if not (workspace / name).exists():
                findings.append(Finding("P1", "missing_module_file", name, f"模块 `{module}` 已启用但缺少文件。"))
    if "review" in enabled and not (workspace / "reports").exists():
        findings.append(Finding("P2", "missing_reports_dir", "reports/", "review 模块已启用但缺少目录。"))
    if "scripts" in enabled and not (workspace / "scripts").exists():
        findings.append(Finding("P2", "missing_scripts_dir", "scripts/", "scripts 模块已启用但缺少目录。"))

    specs_dir = workspace / "specs"
    if not specs_dir.exists():
        findings.append(Finding("P1", "missing_specs_dir", "specs/", "缺少 specs 目录。"))
        return findings + check_handoff(workspace)
    records, parse_findings = parse_specs(specs_dir)
    findings.extend(parse_findings)
    if not records:
        findings.append(Finding("P3", "no_specs", "specs/", "当前没有功能 spec。"))
    for record in records:
        findings.extend(check_spec(record))

    by_id: dict[str, list[SpecRecord]] = {}
    for record in records:
        if record.spec_id:
            by_id.setdefault(record.spec_id, []).append(record)
    for spec_id, matches in by_id.items():
        if len(matches) > 1:
            findings.append(Finding("P1", "duplicate_spec_id", "specs/", f"spec_id `{spec_id}` 出现 {len(matches)} 次。"))

    known_ids = set(by_id)
    for record in records:
        parent = str(record.metadata.get("parent", "none"))
        if parent not in {"none", "project"} and parent not in known_ids:
            findings.append(Finding("P1", "broken_parent", str(record.path), f"父 spec `{parent}` 不存在。"))
        for ref in list_value(record.metadata.get("extends", [])):
            if ref not in known_ids and ref not in {"project", "none"}:
                findings.append(Finding("P1", "broken_extends", str(record.path), f"extends 引用 `{ref}` 不存在。"))

    index = index_entries(workspace / "SPEC_INDEX.md")
    indexed = set(index)
    for spec_id in sorted(known_ids - indexed):
        findings.append(Finding("P1", "unindexed_spec", "SPEC_INDEX.md", f"spec `{spec_id}` 未进入索引。"))
    for spec_id in sorted(indexed - known_ids):
        findings.append(Finding("P1", "orphan_index_entry", "SPEC_INDEX.md", f"索引项 `{spec_id}` 没有对应 spec。"))
    for spec_id in sorted(known_ids & indexed):
        actual_states = {record.status for record in by_id[spec_id]}
        if index[spec_id] not in actual_states:
            findings.append(
                Finding(
                    "P1",
                    "index_status_mismatch",
                    "SPEC_INDEX.md",
                    f"索引状态 `{index[spec_id]}` 与 spec `{spec_id}` 的状态不一致。",
                )
            )
    findings.extend(check_handoff(workspace))
    return findings


def should_fail(findings: list[Finding], strict: bool) -> bool:
    failing = {"P0", "P1"}
    if strict:
        failing.add("P2")
    return any(item.severity in failing for item in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查目标项目的 .vibe-spec。")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="P2 也作为失败。")
    parser.add_argument("--quiet", action="store_true", help="无问题时不输出。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    findings = check_workspace(target / ".vibe-spec")
    failed = should_fail(findings, args.strict)
    result = CommandResult(
        not failed,
        "check",
        changes=[],
        findings=[asdict(item) for item in findings],
        next_actions=[] if not findings else ["按严重级别修复 finding 后重新运行检查"],
    )
    if args.json:
        emit_result(result, True)
    elif findings or not args.quiet:
        emit_result(result, False)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
