#!/usr/bin/env python3
"""扫描代码层级并输出 FILE_MAP 候选，不修改项目事实文件。"""

from __future__ import annotations

import argparse
from pathlib import Path

from vibe_spec_core import CommandResult, emit_result


IGNORED = {
    ".git",
    ".vibe-spec",
    ".worktrees",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".venv",
    "venv",
}

MANIFESTS = {
    "package.json": "JavaScript/TypeScript 项目清单",
    "pyproject.toml": "Python 项目与工具配置",
    "requirements.txt": "Python 依赖清单",
    "Cargo.toml": "Rust 项目清单",
    "go.mod": "Go 模块清单",
    "pom.xml": "Maven 项目清单",
    "build.gradle": "Gradle 构建配置",
    "Dockerfile": "容器构建入口",
    "docker-compose.yml": "本地服务编排",
    "Makefile": "项目任务入口",
}

HIERARCHY_DIRS = {
    "app",
    "apps",
    "cmd",
    "lib",
    "packages",
    "scripts",
    "src",
    "test",
    "tests",
}


def candidate_paths(target: Path) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for path in sorted(target.iterdir(), key=lambda item: item.name.lower()):
        if path.name in IGNORED or path.name.startswith("."):
            continue
        if path.is_dir():
            candidates.append(
                {"path": f"{path.name}/", "type": "目录", "suggested_purpose": "请 Agent 核对职责"}
            )
            if path.name in HIERARCHY_DIRS:
                children = [child for child in path.iterdir() if child.name not in IGNORED and not child.name.startswith(".")]
                for child in sorted(children, key=lambda item: item.name.lower())[:30]:
                    candidates.append(
                        {
                            "path": f"{path.name}/{child.name}{'/' if child.is_dir() else ''}",
                            "type": "子目录" if child.is_dir() else "代码/配置文件",
                            "suggested_purpose": "请 Agent 核对职责",
                        }
                    )
        elif path.name in MANIFESTS:
            candidates.append(
                {"path": path.name, "type": "项目入口", "suggested_purpose": MANIFESTS[path.name]}
            )
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="输出代码地图候选，不修改 FILE_MAP.md。")
    parser.add_argument("target", nargs="?", default=".", help="目标仓库路径。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON。")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"target is not a directory: {target}")
    candidates = candidate_paths(target)
    emit_result(
        CommandResult(
            True,
            "context",
            changes=candidates,
            next_actions=["核对候选职责后再合并到 .vibe-spec/FILE_MAP.md"],
        ),
        as_json=args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
