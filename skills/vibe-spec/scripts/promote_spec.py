#!/usr/bin/env python3
"""按显式状态机和内容门禁推进 spec。"""

from __future__ import annotations

import argparse
from pathlib import Path

from vibe_spec_core import (
    CommandResult,
    SpecError,
    atomic_write_many,
    append_lifecycle,
    append_section_line,
    command_error,
    emit_result,
    find_spec,
    next_action,
    new_verification_id,
    render_spec_index,
    today,
    validate_transition,
    workspace_path,
)


def promote(
    target: Path,
    spec_id: str,
    new_state: str,
    reason: str,
    evidence: str,
    actor: str,
) -> tuple[str, str, Path]:
    spec = find_spec(target, spec_id)
    old_state = spec.status
    findings = validate_transition(spec, new_state)
    if findings:
        raise SpecError("; ".join(findings))

    event_date = today()
    spec.metadata["status"] = new_state
    spec.metadata["updated"] = event_date
    spec.metadata["owner_agent"] = actor
    if new_state == "verified":
        spec.metadata["verification_id"] = new_verification_id()
    spec.body = append_lifecycle(spec.body, event_date, old_state, new_state, reason, evidence)
    spec.body = append_section_line(
        spec.body,
        "Changelog",
        f"- {event_date}: `{old_state}` -> `{new_state}` ({reason})。",
    )
    index_path = workspace_path(target) / "SPEC_INDEX.md"
    atomic_write_many(
        {
            spec.path: spec.text.rstrip() + "\n",
            index_path: render_spec_index(target, upsert=spec),
        }
    )
    return old_state, new_state, spec.path


def main() -> int:
    parser = argparse.ArgumentParser(description="按门禁推进 vibe-spec 状态。")
    parser.add_argument("target", help="目标项目路径。")
    parser.add_argument("spec_id", help="目标 spec ID。")
    parser.add_argument("state", help="目标状态。")
    parser.add_argument("--reason", required=True, help="状态变化原因。")
    parser.add_argument("--evidence", default="none", help="验证、审核或决策证据。")
    parser.add_argument("--actor", default="unspecified", help="执行推进的 Agent 或人员。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()

    try:
        old_state, new_state, path = promote(
            target,
            args.spec_id,
            args.state,
            args.reason,
            args.evidence,
            args.actor,
        )
    except (OSError, SpecError) as exc:
        return command_error("promote", str(exc), args.json)

    emit_result(
        CommandResult(
            True,
            "promote",
            changes=[
                {
                    "spec_id": args.spec_id,
                    "from": old_state,
                    "to": new_state,
                    "path": str(path.relative_to(target)),
                }
            ],
            next_actions=[next_action(new_state)],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
