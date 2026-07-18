#!/usr/bin/env python3
"""显式安装可移植的 vibe-spec Git hooks。"""

from __future__ import annotations

import argparse
import shutil
import stat
import subprocess
from pathlib import Path

from vibe_spec_core import CommandResult, SpecError, command_error, emit_result, workspace_path


MARKER = "managed-by-vibe-spec"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def git_common_dir(target: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--git-common-dir"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SpecError("目标目录不是 Git 仓库")
    path = Path(completed.stdout.strip())
    return path.resolve() if path.is_absolute() else (target / path).resolve()


def display_path(path: Path, target: Path) -> str:
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def hook_text(strict: bool) -> str:
    flag = " --strict" if strict else ""
    return "\n".join(
        [
            "#!/bin/sh",
            f"# {MARKER}",
            "root=$(git rev-parse --show-toplevel) || exit 1",
            f'exec python3 "$root/.vibe-spec/scripts/check_vibe_spec.py" "$root"{flag}',
            "",
        ]
    )


def install_hooks(target: Path, force: bool) -> list[Path]:
    hooks_dir = git_common_dir(target) / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    destinations = [hooks_dir / "pre-commit", hooks_dir / "pre-push"]
    unmanaged = [
        path
        for path in destinations
        if path.exists() and MARKER not in path.read_text(encoding="utf-8", errors="replace")
    ]
    if unmanaged and not force:
        raise SpecError("拒绝覆盖已有非 vibe-spec hook: " + ", ".join(path.name for path in unmanaged))

    backups = [(path, path.with_name(path.name + ".pre-vibe-spec")) for path in unmanaged]
    conflicts = [backup for _, backup in backups if backup.exists()]
    if conflicts:
        raise SpecError("备份文件已存在，拒绝覆盖: " + ", ".join(str(path) for path in conflicts))

    workspace_scripts = workspace_path(target) / "scripts"
    workspace_scripts.mkdir(parents=True, exist_ok=True)
    for name in ("vibe_spec_core.py", "check_vibe_spec.py"):
        source = skill_root() / "scripts" / name
        destination = workspace_scripts / name
        if not destination.exists():
            shutil.copyfile(source, destination)

    for path, backup in backups:
        path.replace(backup)

    for path, strict in ((destinations[0], False), (destinations[1], True)):
        path.write_text(hook_text(strict), encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return destinations


def main() -> int:
    parser = argparse.ArgumentParser(description="显式安装 vibe-spec pre-commit/pre-push hooks。")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--force", action="store_true", help="备份并替换已有非 vibe-spec hook。")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        hooks = install_hooks(target, args.force)
    except (OSError, SpecError) as exc:
        return command_error("hooks", str(exc), args.json)
    emit_result(
        CommandResult(
            True,
            "hooks",
            changes=[{"path": display_path(path, target)} for path in hooks],
            next_actions=["提交前运行快速检查，推送前运行严格检查"],
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
