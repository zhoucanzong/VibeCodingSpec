#!/usr/bin/env python3
"""生成不包含实现者结论的独立审查上下文。"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    command_error,
    emit_result,
    find_spec,
    section_content,
    today,
    workspace_path,
)


REVIEW_SECTIONS = (
    "Summary",
    "Context",
    "Goals",
    "Non-Goals",
    "Requirements",
    "Acceptance Criteria",
    "Verification Plan",
)


def available_context_path(reports: Path, event_date: str, spec_id: str) -> Path:
    base = reports / f"{event_date}-{spec_id}-review-context.md"
    if not base.exists():
        return base
    counter = 2
    while (reports / f"{event_date}-{spec_id}-review-context-{counter}.md").exists():
        counter += 1
    return reports / f"{event_date}-{spec_id}-review-context-{counter}.md"


def git_diff_stat(target: Path, base: str | None) -> str:
    command = ["git", "-C", str(target), "diff", "--stat"]
    if base:
        command.append(base)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip() or "no unstaged diff"


def prepare_context(target: Path, spec_id: str, base: str | None, output: Path | None) -> Path:
    spec = find_spec(target, spec_id)
    workspace = workspace_path(target)
    if output is None:
        destination = available_context_path(workspace / "reports", today(), spec_id)
    else:
        destination = output if output.is_absolute() else target / output
        destination = destination.resolve()
        try:
            destination.relative_to(target)
        except ValueError as exc:
            raise SpecError("review context 输出必须位于目标仓库内") from exc
        if destination.exists():
            raise SpecError(f"输出文件已存在，拒绝覆盖: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Independent Review Context: {spec_id}",
        "",
        "审查者只根据以下规格、变更摘要和验证目标作出判断。不要采纳实现者的结论。",
        "",
        "## Metadata",
        "",
        f"- status: `{spec.status}`",
        f"- parent: `{spec.metadata.get('parent', 'none')}`",
        f"- spec: `{spec.path.relative_to(target)}`",
        "",
    ]
    related: set[str] = set()
    for heading in REVIEW_SECTIONS:
        content = section_content(spec.body, heading)
        if content is None:
            continue
        lines.extend([f"## {heading}", "", content, ""])
        related.update(re.findall(r"`([^`]+[/.][^`]*)`", content))
    lines.extend(["## Git Diff Stat", "", "```text", git_diff_stat(target, base), "```", ""])
    lines.extend(["## Related Files", ""])
    lines.extend([f"- `{path}`" for path in sorted(related)] or ["- none identified"])
    lines.append("")
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="准备独立 review 上下文。")
    parser.add_argument("target", help="目标项目路径。")
    parser.add_argument("spec_id", help="目标 spec ID。")
    parser.add_argument("--base", help="可选 Git diff 基线。")
    parser.add_argument("--output", type=Path, help="可选输出路径。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        destination = prepare_context(target, args.spec_id, args.base, args.output)
    except (OSError, SpecError) as exc:
        return command_error("review-context", str(exc), args.json)
    emit_result(
        CommandResult(
            True,
            "review-context",
            changes=[{"path": str(destination.relative_to(target))}],
            next_actions=["把该文件交给独立 subagent；不可附带实现者结论"],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
