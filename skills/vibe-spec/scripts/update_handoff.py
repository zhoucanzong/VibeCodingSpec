#!/usr/bin/env python3
"""更新跨 Agent HANDOFF 的当前工作章节。"""

from __future__ import annotations

import argparse
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    command_error,
    emit_result,
    find_spec,
    replace_section,
    section_content,
    workspace_path,
)
from work_records import history_path, read_record, record_lock, resolve_record, write_record_with_history


def update_handoff(
    target: Path,
    goal: str,
    state: str,
    next_action: str,
    active_specs: list[str],
    blockers: list[str],
    verifications: list[str],
    risks: list[str],
) -> Path:
    workspace = workspace_path(target)
    if workspace.is_symlink():
        raise SpecError(".vibe-spec must not be a symlink")
    if not (workspace / "HANDOFF.md").exists():
        raise SpecError("缺少 HANDOFF.md，请先运行 init")
    handoff = resolve_record(workspace, "HANDOFF.md")
    for spec_id in active_specs:
        if spec_id != "project":
            find_spec(target, spec_id)

    sections = {
        "Current Goal": goal,
        "Active Specs": "\n".join(f"- {item}" for item in active_specs) if active_specs else "- none",
        "Working State": state,
        "Recent Verification": "\n".join(f"- {item}" for item in verifications) if verifications else "- none",
        "Blockers": "\n".join(f"- {item}" for item in blockers) if blockers else "- none",
        "Worktree Risks": "\n".join(f"- {item}" for item in risks) if risks else "- none",
        "Next Action": next_action,
    }
    with record_lock(workspace, handoff):
        if not handoff.is_file():
            raise SpecError("缺少 HANDOFF.md，请先运行 init")
        original = read_record(handoff)
        text = original
        for heading, content in sections.items():
            if section_content(text, heading) != content.strip():
                text = replace_section(text, heading, content)
        if text != original:
            history = history_path(workspace, "handoffs")
            write_record_with_history(workspace, handoff, text, history, original)
    return handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="更新跨 Agent 项目交接。")
    parser.add_argument("target", help="目标项目路径。")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--active-spec", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    parser.add_argument("--verification", action="append", default=[])
    parser.add_argument("--risk", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        handoff = update_handoff(
            target,
            args.goal,
            args.state,
            args.next_action,
            args.active_spec,
            args.blocker,
            args.verification,
            args.risk,
        )
    except (OSError, SpecError, UnicodeError) as exc:
        return command_error("handoff", str(exc), args.json)
    emit_result(
        CommandResult(
            True,
            "handoff",
            changes=[{"path": str(handoff.relative_to(target)), "state": args.state}],
            next_actions=[args.next_action],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
