#!/usr/bin/env python3
"""从模板创建唯一 spec 并同步索引。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    all_specs,
    command_error,
    emit_result,
    rebuild_spec_index,
    today,
    workspace_path,
)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_spec_id(raw: str) -> str:
    value = raw.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)
    if not value:
        raise SpecError("spec_id 必须包含英文字母或数字")
    if len(value) > 64:
        raise SpecError("spec_id 最长 64 个字符")
    return value


def create_spec(
    target: Path,
    raw_spec_id: str,
    title: str,
    parent: str,
    owner_agent: str,
) -> Path:
    workspace = workspace_path(target)
    if not workspace.exists():
        raise SpecError("缺少 .vibe-spec，请先运行 init")
    spec_id = normalize_spec_id(raw_spec_id)
    if any(spec.spec_id == spec_id for spec in all_specs(target)):
        raise SpecError(f"spec_id `{spec_id}` 已存在")
    if parent not in {"none", "project"} and not any(spec.spec_id == parent for spec in all_specs(target)):
        raise SpecError(f"父 spec `{parent}` 不存在")

    event_date = today()
    template = (skill_root() / "assets" / "templates" / "FEATURE_SPEC.md").read_text(encoding="utf-8")
    rendered = (
        template.replace("spec_id: short-kebab-title", f"spec_id: {spec_id}")
        .replace("parent: none", f"parent: {parent}")
        .replace("created: YYYY-MM-DD", f"created: {event_date}")
        .replace("updated: YYYY-MM-DD", f"updated: {event_date}")
        .replace("owner_agent: unspecified", f"owner_agent: {owner_agent}")
        .replace("# Spec: 标题", f"# Spec: {title}")
        .replace("| YYYY-MM-DD | none | draft | unspecified | 创建 spec | 本文件 |", f"| {event_date} | none | draft | {owner_agent} | 创建 spec | 本文件 |")
        .replace("- YYYY-MM-DD: 创建 spec。", f"- {event_date}: 创建 spec。")
    )
    destination = workspace / "specs" / f"{event_date}-{spec_id}.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    rebuild_spec_index(target)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="创建新的 vibe-spec 功能规格。")
    parser.add_argument("target", help="目标项目路径。")
    parser.add_argument("spec_id", help="稳定的英文 kebab-case ID；输入会规范化。")
    parser.add_argument("--title", required=True, help="Spec 标题。")
    parser.add_argument("--parent", default="project", help="父 spec ID，默认 project。")
    parser.add_argument("--owner-agent", default="unspecified", help="当前负责 Agent。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()

    try:
        destination = create_spec(target, args.spec_id, args.title, args.parent, args.owner_agent)
    except (OSError, SpecError) as exc:
        return command_error("spec", str(exc), args.json)

    relative = destination.relative_to(target)
    emit_result(
        CommandResult(
            True,
            "spec",
            changes=[{"path": str(relative), "spec_id": normalize_spec_id(args.spec_id), "status": "draft"}],
            next_actions=["由 Agent 补齐规格内容，再推进到 ready_for_review"],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
