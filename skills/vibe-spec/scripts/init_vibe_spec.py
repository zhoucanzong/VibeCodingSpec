#!/usr/bin/env python3
"""Initialize a .vibe-spec workspace in a target repository."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TEMPLATE_FILES = [
    "PROJECT_SPEC.md",
    "AGENT_GUIDE.md",
    "STYLE_GUIDE.md",
    "DECISIONS.md",
    "LIFECYCLE.md",
    "FILE_MAP.md",
    "DATA_GUIDE.md",
    "TESTING_GUIDE.md",
    "EXPERIMENTS.md",
    "SPEC_INDEX.md",
]


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_if_missing(src: Path, dst: Path) -> str:
    if dst.exists():
        return f"kept     {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return f"created  {dst}"


def init_workspace(target: Path) -> list[str]:
    templates = skill_root() / "assets" / "templates"
    workspace = target / ".vibe-spec"
    specs = workspace / "specs"
    reports = workspace / "reports"
    scripts = workspace / "scripts"
    messages: list[str] = []

    workspace.mkdir(parents=True, exist_ok=True)
    specs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)

    messages.append(f"ensured  {workspace}")
    messages.append(f"ensured  {specs}")
    messages.append(f"ensured  {reports}")
    messages.append(f"ensured  {scripts}")

    for name in TEMPLATE_FILES:
        messages.append(copy_if_missing(templates / name, workspace / name))

    messages.append(copy_if_missing(templates / "FEATURE_SPEC.md", specs / "example-feature-spec.md"))
    messages.append(copy_if_missing(templates / "REVIEW_REPORT.md", reports / "review-report-template.md"))
    messages.append(copy_if_missing(templates / "AUDIT_REPORT.md", reports / "audit-report-template.md"))

    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize .vibe-spec in a target repository.")
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target repository path. Defaults to the current directory.",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        parser.error(f"target does not exist: {target}")
    if not target.is_dir():
        parser.error(f"target is not a directory: {target}")

    for message in init_workspace(target):
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
