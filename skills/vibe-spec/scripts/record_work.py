#!/usr/bin/env python3
"""Append a work event and its immutable evidence record."""

from __future__ import annotations

import argparse
from pathlib import Path

from vibe_spec_core import CommandResult, SpecError, command_error, emit_result
from work_records import record_work


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    parser.add_argument("record", help="Markdown path relative to .vibe-spec")
    parser.add_argument("--actor", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--next-action")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        record, history = record_work(target, args.record, args.actor, args.event,
                                      args.summary, args.evidence, args.next_action)
    except (OSError, SpecError, UnicodeError, ValueError) as exc:
        return command_error("record-work", str(exc), args.json)
    emit_result(CommandResult(True, "record-work", changes=[
        {"path": str(record.relative_to(target)), "action": "append"},
        {"path": str(history.relative_to(target)), "action": "create"},
    ], next_actions=[args.next_action] if args.next_action else []), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
