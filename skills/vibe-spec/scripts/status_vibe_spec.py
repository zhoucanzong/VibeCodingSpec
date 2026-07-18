#!/usr/bin/env python3
"""汇总 spec、handoff 和 roadmap 的项目状态。"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    all_specs,
    command_error,
    emit_result,
    section_content,
    workspace_path,
)


def list_items(content: str | None) -> list[str]:
    if not content:
        return []
    return [line[2:].strip() for line in content.splitlines() if line.startswith("- ") and line[2:].strip() != "none"]


def roadmap_items(content: str | None) -> list[str]:
    if not content:
        return []
    items: list[str] = []
    for line in content.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"项目", "---", "none"}:
            continue
        items.append(cells[0])
    return items


def status_summary(target: Path) -> dict[str, object]:
    workspace = workspace_path(target)
    handoff_path = workspace / "HANDOFF.md"
    roadmap_path = workspace / "ROADMAP.md"
    if not handoff_path.exists() or not roadmap_path.exists():
        raise SpecError("缺少 HANDOFF.md 或 ROADMAP.md，请重新运行 init")
    handoff = handoff_path.read_text(encoding="utf-8")
    roadmap = roadmap_path.read_text(encoding="utf-8")
    states = Counter(spec.status for spec in all_specs(target))
    blockers = list_items(section_content(handoff, "Blockers"))
    return {
        "states": dict(sorted(states.items())),
        "current_goal": (section_content(handoff, "Current Goal") or "unknown").strip(),
        "working_state": (section_content(handoff, "Working State") or "unknown").strip(),
        "active_specs": list_items(section_content(handoff, "Active Specs")),
        "blockers": blockers,
        "next_action": (section_content(handoff, "Next Action") or "unknown").strip(),
        "roadmap_now": roadmap_items(section_content(roadmap, "Now")),
        "roadmap_next": roadmap_items(section_content(roadmap, "Next")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="汇总 vibe-spec 项目上下文。")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        summary = status_summary(target)
    except (OSError, SpecError) as exc:
        return command_error("status", str(exc), args.json)
    next_actions = [str(summary["next_action"])]
    if summary["blockers"]:
        next_actions.insert(0, "先处理 HANDOFF.md 中的阻塞项")
    emit_result(CommandResult(True, "status", changes=[summary], next_actions=next_actions), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
