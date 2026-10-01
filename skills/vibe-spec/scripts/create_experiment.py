#!/usr/bin/env python3
"""建立实验计划、逐次运行或结论草稿；不执行实验、不填造结果。"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

from experiment_core import ID, TERMINAL_RUNS, conclusion_digest, digest_file, present, read_record, within
from vibe_spec_core import (
    CommandResult, SpecError, atomic_write_many, command_error, emit_result,
    find_spec, parse_frontmatter, render_frontmatter, replace_section, section_content, workspace_path,
)
from work_records import record_lock


def identifier(value: str) -> str:
    if not ID.fullmatch(value) or value.lower() == "templates":
        raise SpecError("ID 仅允许字母、数字、连字符和下划线，不能使用 templates")
    return value


def create_record(target: Path, experiment_id: str, kind: str, record_id: str | None,
                  owner: str, title: str = "", spec_id: str = "project") -> Path:
    workspace = workspace_path(target)
    index = workspace / "EXPERIMENTS.md"
    if not index.is_file():
        raise SpecError("请先启用 experiments 模块")
    if not present(owner) or any(char in owner + title + spec_id for char in "\r\n"):
        raise SpecError("owner 必须有效，owner/title/spec 不能包含换行")
    directory = within(workspace, f"experiments/{identifier(experiment_id)}")
    plan_path = directory / "PLAN.md"
    if kind != "plan" and record_id is None:
        raise SpecError("run/conclusion 需要 --record-id")
    template_name = {"plan": "EXPERIMENT_PLAN.md", "run": "EXPERIMENT_RUN.md",
                     "conclusion": "EXPERIMENT_CONCLUSION.md"}[kind]
    source = Path(__file__).resolve().parents[1] / "assets" / "templates" / template_name
    metadata, body = parse_frontmatter(source.read_text(encoding="utf-8"))
    metadata.update(experiment_id=experiment_id, created=datetime.now(timezone.utc).isoformat())
    files = {}
    with record_lock(workspace, index), record_lock(workspace, plan_path), ExitStack() as run_locks:
        if kind == "plan":
            if directory.exists():
                raise SpecError("实验 ID 已存在，拒绝覆盖")
            if not present(title):
                raise SpecError("计划需要 --title")
            if spec_id != "project":
                find_spec(target, spec_id)
            metadata.update(owner=owner, spec_id=spec_id)
            body = body.replace("# 实验计划", f"# {title}", 1)
            destination = plan_path
            files[index] = index.read_text(encoding="utf-8").rstrip() + (
                f"\n\n- [{experiment_id}](experiments/{experiment_id}/PLAN.md)：{title}。"
                "状态与逐次运行见计划；完成后补入结论链接。\n"
            )
        else:
            plan, plan_body = read_record(plan_path)
            if plan.get("experiment_id") != experiment_id or plan.get("archived") == "true":
                raise SpecError("计划身份无效或已归档")
            rid = identifier(record_id)
            subdir = "runs" if kind == "run" else "conclusions"
            destination = within(workspace, f"experiments/{experiment_id}/{subdir}/{rid}.md")
            if destination.exists():
                raise SpecError("记录 ID 已存在；重跑或新结论必须使用新 ID")
            if kind == "run":
                if plan.get("status") not in {"planned", "running"}:
                    raise SpecError("已结束实验需先记录重开原因并重新规划")
                if any(not present(section_content(plan_body, h)) for h in
                       ("Question", "Hypothesis", "Design", "Decision Rule", "Budget")):
                    raise SpecError("运行前必须补齐计划问题、假设、设计、判定标准和预算")
                digest = digest_file(plan_path)
                snapshot = within(workspace, f"experiments/{experiment_id}/plans/{digest}.md")
                if snapshot.exists():
                    if digest_file(snapshot) != digest:
                        raise SpecError("已有计划快照损坏，拒绝覆盖")
                else:
                    files[snapshot] = plan_path.read_bytes().decode("utf-8")
                metadata.update(run_id=rid, owner=owner, plan_sha256=digest,
                                plan_snapshot=snapshot.relative_to(workspace).as_posix())
            else:
                rows = ["| Run ID | SHA256 | Snapshot |", "|---|---|---|"]
                for run_path in sorted((directory / "runs").glob("*.md")):
                    within(workspace, run_path.relative_to(workspace).as_posix())
                    run_locks.enter_context(record_lock(workspace, run_path))
                    run, _ = read_record(run_path)
                    if run.get("status") not in TERMINAL_RUNS:
                        raise SpecError("仍有未结束运行，先等待或记录真实中断状态")
                    if run.get("experiment_id") != experiment_id or run.get("run_id") != run_path.stem:
                        raise SpecError("运行记录身份无效")
                    digest = digest_file(run_path)
                    snapshot = within(workspace, f"experiments/{experiment_id}/evidence/{run_path.stem}/{digest}.md")
                    if snapshot.exists():
                        if digest_file(snapshot) != digest:
                            raise SpecError("已有运行证据快照损坏，拒绝覆盖")
                    else:
                        files[snapshot] = run_path.read_bytes().decode("utf-8")
                    rows.append(f"| {run_path.stem} | {digest} | {snapshot.relative_to(workspace).as_posix()} |")
                if len(rows) == 2:
                    raise SpecError("没有终态运行，不能生成实验结论")
                metadata.update(conclusion_id=rid, author=owner)
                body = replace_section(body, "Run Evidence", "\n".join(rows))
        files[destination] = render_frontmatter(metadata) + body
        atomic_write_many(files)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="创建实验记录或计算结论审阅摘要。")
    parser.add_argument("target")
    parser.add_argument("experiment_id")
    parser.add_argument("--kind", choices=["plan", "run", "conclusion", "digest"], default="plan")
    parser.add_argument("--record-id")
    parser.add_argument("--owner", default="unknown")
    parser.add_argument("--title", default="")
    parser.add_argument("--spec", default="project")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    try:
        if args.kind == "digest":
            if not args.record_id:
                raise SpecError("digest 需要 --record-id")
            path = within(workspace_path(target), f"experiments/{identifier(args.experiment_id)}/conclusions/{identifier(args.record_id)}.md")
            data, body = read_record(path)
            changes = [{"path": str(path), "conclusion_sha256": conclusion_digest(data, body)}]
        else:
            path = create_record(target, args.experiment_id, args.kind, args.record_id,
                                 args.owner, args.title, args.spec)
            changes = [{"path": str(path)}]
    except (OSError, UnicodeError, SpecError) as exc:
        return command_error("experiment", str(exc), args.json)
    emit_result(CommandResult(True, "experiment", changes=changes,
                              next_actions=["按实验协议补齐事实、执行与证据；草稿不代表已执行或已审阅"]), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
