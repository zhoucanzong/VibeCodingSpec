#!/usr/bin/env python3
"""按 profile/module 初始化目标仓库的 .vibe-spec 工作区。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from vibe_spec_core import CommandResult, emit_result


MODULE_FILES = {
    "core": [
        ("PROJECT_SPEC.md", ""),
        ("AGENT_GUIDE.md", ""),
        ("STYLE_GUIDE.md", ""),
        ("LIFECYCLE.md", ""),
        ("SPEC_INDEX.md", ""),
        ("MODULES.md", ""),
        ("HANDOFF.md", ""),
        ("ROADMAP.md", ""),
    ],
    "memory": [
        ("DECISIONS.md", ""),
        ("FILE_MAP.md", ""),
    ],
    "testing": [
        ("TESTING_GUIDE.md", ""),
    ],
    "review": [
        ("REVIEW_REPORT.md", "reports/review-report-template.md"),
        ("AUDIT_REPORT.md", "reports/audit-report-template.md"),
    ],
    "data": [
        ("DATA_GUIDE.md", ""),
    ],
    "experiments": [
        ("EXPERIMENTS.md", ""),
    ],
    "security": [
        ("SECURITY_GUIDE.md", ""),
    ],
    "release": [
        ("RELEASE_GUIDE.md", ""),
    ],
    "migration": [
        ("MIGRATION_GUIDE.md", ""),
    ],
    "environment": [
        ("ENVIRONMENT_GUIDE.md", ""),
    ],
    "observability": [
        ("OBSERVABILITY_GUIDE.md", ""),
    ],
    "contracts": [
        ("CONTRACTS.md", ""),
    ],
    "scripts": [],
}

PROFILES = {
    "minimal": ["core"],
    "standard": ["core", "memory", "testing", "review"],
    "production": [
        "core",
        "memory",
        "testing",
        "review",
        "data",
        "experiments",
        "security",
        "release",
        "migration",
        "environment",
        "observability",
        "contracts",
        "scripts",
    ],
}

MODULE_ALIASES = {
    "experiment": "experiments",
    "exp": "experiments",
    "test": "testing",
    "tests": "testing",
    "reviews": "review",
    "audit": "review",
    "contract": "contracts",
    "api": "contracts",
    "env": "environment",
    "deploy": "release",
    "deployment": "release",
    "migrations": "migration",
    "observe": "observability",
    "monitoring": "observability",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_if_missing(src: Path, dst: Path) -> str:
    if dst.exists():
        return f"kept     {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return f"created  {dst}"


def normalize_modules(module_names: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw_name in module_names:
        for part in raw_name.split(","):
            name = part.strip().lower()
            if not name:
                continue
            name = MODULE_ALIASES.get(name, name)
            if name not in MODULE_FILES:
                valid = ", ".join(sorted(MODULE_FILES))
                raise ValueError(f"unknown module: {part}. Valid modules: {valid}")
            if name not in normalized:
                normalized.append(name)
    return normalized


def resolve_modules(profile: str, extra_modules: list[str]) -> list[str]:
    if profile not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile: {profile}. Valid profiles: {valid}")

    modules = list(PROFILES[profile])
    for module in normalize_modules(extra_modules):
        if module not in modules:
            modules.append(module)
    return modules


def target_path(workspace: Path, relative_target: str, template_name: str) -> Path:
    if relative_target:
        return workspace / relative_target
    return workspace / template_name


def update_modules_file(workspace: Path, profile: str, modules: list[str]) -> str:
    modules_file = workspace / "MODULES.md"
    if not modules_file.exists():
        return f"skipped  {modules_file}"

    current = modules_file.read_text(encoding="utf-8")
    can_rewrite = "TBD" in current or "本次初始化启用" in current or "未启用，可后续追加" in current
    if not can_rewrite:
        with modules_file.open("a", encoding="utf-8") as file:
            file.write(
                "\n## 启用记录\n\n"
                f"- profile: `{profile}`; modules: `{','.join(modules)}`\n"
            )
        return f"appended {modules_file}"

    enabled = set(modules)
    lines = [
        "# 模块配置",
        "",
        "用于记录当前项目启用了哪些 vibe-spec 治理模块。",
        "",
        "## Profile",
        "",
        profile,
        "",
        "## Enabled Modules",
        "",
        "| 模块 | 是否启用 | 用途 | 备注 |",
        "|---|---|---|---|",
    ]
    descriptions = {
        "core": "项目规格、生命周期、Agent 接手和 spec 索引",
        "memory": "决策记录和文件地图",
        "testing": "测试命令、fixtures 和验证脚本",
        "review": "review/audit 报告模板",
        "data": "数据、schema、隐私和生成产物",
        "experiments": "实验、benchmark 和评估记录",
        "security": "安全、隐私和权限",
        "release": "发布、回滚和灰度",
        "migration": "数据库迁移和 backfill",
        "environment": "环境变量和配置",
        "observability": "日志、指标和告警",
        "contracts": "API、事件和外部集成契约",
        "scripts": "`.vibe-spec/scripts/` 辅助脚本目录",
    }
    for module in MODULE_FILES:
        is_enabled = "yes" if module in enabled else "no"
        notes = "本次初始化启用" if module in enabled else "未启用，可后续追加"
        lines.append(f"| {module} | {is_enabled} | {descriptions[module]} | {notes} |")

    lines.extend(
        [
            "",
            "## 维护规则",
            "",
            "- 启用新模块时，把相关文件加入 `.vibe-spec/` 并更新本文件。",
            "- 不建议自动删除已启用模块；如果不再使用，标记为 disabled 并说明原因。",
            "- 高风险生产项目优先启用 security、release、migration、environment、observability。",
        ]
    )
    modules_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"updated  {modules_file}"


def init_workspace(target: Path, profile: str, extra_modules: list[str]) -> list[str]:
    templates = skill_root() / "assets" / "templates"
    workspace = target / ".vibe-spec"
    modules = resolve_modules(profile, extra_modules)
    messages: list[str] = []

    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "specs").mkdir(parents=True, exist_ok=True)
    messages.append(f"profile  {profile}")
    messages.append(f"modules  {','.join(modules)}")
    messages.append(f"ensured  {workspace}")
    messages.append(f"ensured  {workspace / 'specs'}")

    if "review" in modules:
        (workspace / "reports").mkdir(parents=True, exist_ok=True)
        messages.append(f"ensured  {workspace / 'reports'}")
    if "scripts" in modules:
        (workspace / "scripts").mkdir(parents=True, exist_ok=True)
        messages.append(f"ensured  {workspace / 'scripts'}")

    for module in modules:
        for template_name, relative_target in MODULE_FILES[module]:
            src = templates / template_name
            dst = target_path(workspace, relative_target, template_name)
            messages.append(copy_if_missing(src, dst))

    if "core" in modules:
        messages.append(update_modules_file(workspace, profile, modules))

    if "scripts" in modules:
        for script in sorted((skill_root() / "scripts").glob("*.py")):
            messages.append(copy_if_missing(script, workspace / "scripts" / script.name))

    return messages


AGENT_ENTRY_FILES = {
    "claude": "CLAUDE.md",
    "codex": "AGENTS.md",
    "cursor": ".cursor/rules/vibe-spec.md",
}


def install_agent_entries(target: Path, agents: list[str]) -> list[str]:
    template = (skill_root() / "assets" / "templates" / "AGENT_ENTRY.md").read_text(encoding="utf-8")
    messages: list[str] = []
    for agent in agents:
        destination = target / AGENT_ENTRY_FILES[agent]
        if destination.exists():
            messages.append(f"kept     {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(template.replace("{{AGENT}}", agent), encoding="utf-8")
        messages.append(f"created  {destination}")
    return messages


def install_ci(target: Path) -> str:
    source = skill_root() / "assets" / "templates" / "github-actions-vibe-spec.yml"
    destination = target / ".github" / "workflows" / "vibe-spec.yml"
    return copy_if_missing(source, destination)


def list_profiles() -> None:
    print("Profiles:")
    for profile, modules in PROFILES.items():
        print(f"  {profile}: {','.join(modules)}")
    print("\nModules:")
    for module in sorted(MODULE_FILES):
        print(f"  {module}")


def main() -> int:
    parser = argparse.ArgumentParser(description="按 profile/module 初始化 .vibe-spec。")
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="目标仓库路径，默认当前目录。",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="standard",
        help="初始化档位：minimal、standard 或 production。默认 standard。",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=[],
        help="在 profile 基础上额外启用模块，支持逗号分隔。",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="列出可用 profile 和 module 后退出。",
    )
    parser.add_argument(
        "--agent-entry",
        nargs="*",
        choices=sorted(AGENT_ENTRY_FILES),
        default=[],
        help="创建可选的跨 Agent 薄入口：claude、codex、cursor。",
    )
    parser.add_argument("--ci", action="store_true", help="安装 GitHub Actions 检查模板。")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON 结果。")
    args = parser.parse_args()

    if args.list_profiles:
        list_profiles()
        return 0

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        parser.error(f"target does not exist: {target}")
    if not target.is_dir():
        parser.error(f"target is not a directory: {target}")

    try:
        messages = init_workspace(target, args.profile, args.modules)
    except ValueError as exc:
        parser.error(str(exc))

    messages.extend(install_agent_entries(target, args.agent_entry))
    if args.ci:
        messages.append(install_ci(target))

    if args.json:
        emit_result(
            CommandResult(
                True,
                "init",
                changes=messages,
                next_actions=["补齐 .vibe-spec/HANDOFF.md 中的当前项目上下文"],
            ),
            as_json=True,
        )
    else:
        for message in messages:
            print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
