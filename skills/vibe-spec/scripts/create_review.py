#!/usr/bin/env python3
"""创建结构化 review 报告并回链目标 spec。"""

from __future__ import annotations

import argparse
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    append_section_line,
    command_error,
    emit_result,
    find_spec,
    today,
    workspace_path,
    write_spec,
)


def available_report_path(reports: Path, event_date: str, spec_id: str) -> Path:
    base = reports / f"{event_date}-{spec_id}-review.md"
    if not base.exists():
        return base
    counter = 2
    while (reports / f"{event_date}-{spec_id}-review-{counter}.md").exists():
        counter += 1
    return reports / f"{event_date}-{spec_id}-review-{counter}.md"


def create_review(
    target: Path,
    spec_id: str,
    verdict: str,
    mode: str,
    summary: str,
    findings: list[str],
) -> Path:
    spec = find_spec(target, spec_id)
    workspace = workspace_path(target)
    reports = workspace / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    event_date = today()
    report_path = available_report_path(reports, event_date, spec_id)
    verdict_label = "PASS" if verdict == "pass" else "NEEDS CHANGES"
    finding_lines = findings or ["none"]
    report = "\n".join(
        [
            "---",
            f"spec_id: {spec_id}",
            f"verdict: {verdict}",
            f"mode: {mode}",
            f"created: {event_date}",
            "---",
            "",
            f"# Review: {spec_id}",
            "",
            "## 结论",
            "",
            verdict_label,
            "",
            "## 审查方式",
            "",
            mode,
            "",
            "## 摘要",
            "",
            summary,
            "",
            "## 问题",
            "",
            *[f"- {finding}" for finding in finding_lines],
            "",
            "## Spec",
            "",
            f"- `{spec.path.relative_to(target)}`",
            f"- review 前状态：`{spec.status}`",
            "",
            "## 后续动作",
            "",
            "- 推进到 `reviewed`。" if verdict == "pass" else "- 修复问题并推进到 `needs_changes`。",
            "",
        ]
    )
    report_path.write_text(report, encoding="utf-8")
    relative_report = report_path.relative_to(target)
    note = f"- {event_date}: {verdict_label} via `{mode}`; report: `{relative_report}`; {summary}"
    spec.body = append_section_line(spec.body, "Review Notes", note)
    spec.metadata["updated"] = event_date
    write_spec(spec)
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="创建 vibe-spec review 报告。")
    parser.add_argument("target", help="目标项目路径。")
    parser.add_argument("spec_id", help="目标 spec ID。")
    parser.add_argument("--verdict", required=True, choices=("pass", "changes"))
    parser.add_argument("--mode", required=True, choices=("subagent", "self"))
    parser.add_argument("--summary", required=True, help="审核摘要。")
    parser.add_argument("--finding", action="append", default=[], help="审核问题，可重复。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        report = create_review(target, args.spec_id, args.verdict, args.mode, args.summary, args.finding)
    except (OSError, SpecError) as exc:
        return command_error("review", str(exc), args.json)

    emit_result(
        CommandResult(
            True,
            "review",
            changes=[{"path": str(report.relative_to(target)), "verdict": args.verdict, "mode": args.mode}],
            next_actions=["由 Agent 核对报告后使用 promote 推进状态"],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
