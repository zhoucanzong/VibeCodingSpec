"""实验 Markdown 的读取、证据绑定和只读一致性检查。"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from vibe_spec_core import SpecError, meaningful, parse_frontmatter, render_frontmatter, section_content

TERMINAL_RUNS = {"completed", "failed", "interrupted", "cancelled"}
PLAN_STATES = {"planned", "running", "completed", "cancelled"}
RUN_STATES = {"planned", "running"} | TERMINAL_RUNS
HASH = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(root: Path, relative: str) -> Path:
    candidate = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts or not candidate.resolve().is_relative_to(root.resolve()):
        raise SpecError(f"路径超出允许范围: {relative}")
    return candidate


def read_record(path: Path) -> tuple[dict, str]:
    data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if any(not isinstance(value, str) for value in data.values()):
        raise SpecError("实验记录 frontmatter 只使用标量字符串")
    return data, body


def conclusion_digest(data: dict, body: str) -> str:
    content = render_frontmatter({key: value for key, value in data.items()
                                 if key not in {"status", "review_evidence"}}) + body
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def table_rows(body: str, heading: str) -> list[list[str]]:
    rows = []
    for line in (section_content(body, heading) or "").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if cells[0] in {"Path", "Run ID"} or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def present(value: str | None) -> bool:
    return bool(value and value.strip() not in {"none", "unknown", "not_measured"} and meaningful(value))


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("时间须含时区")
    return result


def inspect_experiments(workspace: Path, verify_artifacts: bool = False) -> tuple[dict, list[dict]]:
    root = workspace / "experiments"
    findings = []
    summary = {"experiments": {}, "run_states": {}, "archived": []}
    run_states: Counter = Counter()

    def issue(code: str, path: Path, message: str, severity: str = "P2") -> None:
        findings.append({"severity": severity, "code": code,
                         "location": str(path.relative_to(workspace)), "message": message})

    def read(path: Path):
        try:
            within(root, str(path.relative_to(root)))
            return read_record(path)
        except (OSError, UnicodeError, SpecError) as exc:
            issue("invalid_experiment_record", path, str(exc))
            return None

    for directory in sorted(root.iterdir()) if root.exists() else []:
        if not directory.is_dir() or directory.name == "templates":
            continue
        plan_path = directory / "PLAN.md"
        plan = read(plan_path)
        if plan is None:
            continue
        meta, body = plan
        experiment_id = directory.name
        if not ID.fullmatch(experiment_id) or meta.get("experiment_id") != experiment_id:
            issue("invalid_experiment_id", plan_path, "实验 ID 与目录不一致")
        status = meta.get("status", "unknown")
        summary["experiments"][experiment_id] = status
        if status not in PLAN_STATES:
            issue("invalid_experiment_status", plan_path, "未知计划状态")
        spec_id = meta.get("spec_id", "unknown")
        if spec_id != "project":
            from vibe_spec_core import find_spec
            try:
                find_spec(workspace, spec_id)
            except (OSError, SpecError):
                issue("unknown_experiment_spec", plan_path, "实验关联 Spec 不存在或重复")
        if not present(meta.get("owner")):
            issue("missing_experiment_owner", plan_path, "实验需有负责人")
        if status != "planned":
            for heading in ("Question", "Hypothesis", "Design", "Decision Rule", "Budget"):
                if not present(section_content(body, heading)):
                    issue("incomplete_experiment_plan", plan_path, f"缺少 {heading}")

        runs = {}
        for run_path in sorted((directory / "runs").glob("*.md")):
            record = read(run_path)
            if record is None:
                continue
            data, run_body = record
            run_id = run_path.stem
            runs[run_id] = (data, run_body, run_path)
            state = data.get("status", "unknown")
            run_states[state] += 1
            if data.get("experiment_id") != experiment_id or data.get("run_id") != run_id:
                issue("invalid_run_id", run_path, "运行记录身份与路径不一致")
            if state not in RUN_STATES:
                issue("invalid_run_status", run_path, "未知运行状态")
            try:
                snapshot = within(workspace, data.get("plan_snapshot", "unknown"))
                if snapshot.parent != directory / "plans" or digest_file(snapshot) != data.get("plan_sha256"):
                    raise SpecError("计划快照校验值或位置不符")
            except (OSError, SpecError) as exc:
                issue("invalid_plan_snapshot", run_path, str(exc))
            if state == "planned":
                continue
            if state == "cancelled":
                if data.get("started", "unknown") != "unknown" or data.get("exit_code", "unknown") != "unknown":
                    issue("invalid_run_cancellation", run_path, "已启动运行应记 interrupted，不能记为未启动取消")
                try:
                    instant(data.get("ended", "unknown"))
                except ValueError as exc:
                    issue("invalid_run_time", run_path, str(exc))
                if not present(section_content(run_body, "Observations")):
                    issue("missing_run_observations", run_path, "取消需记录实际原因")
                continue
            for key in ("owner", "code_revision", "data_version", "model", "seed"):
                if not present(data.get(key)):
                    issue("incomplete_run", run_path, f"缺少 {key}")
            for heading in ("Configuration", "Environment", "Command"):
                if not present(section_content(run_body, heading)):
                    issue("incomplete_run", run_path, f"缺少 {heading}")
            try:
                started = instant(data.get("started", "unknown"))
                if state in TERMINAL_RUNS and instant(data.get("ended", "unknown")) < started:
                    raise ValueError("结束时间早于开始")
            except ValueError as exc:
                issue("invalid_run_time", run_path, str(exc))
            if state not in TERMINAL_RUNS:
                continue
            code = data.get("exit_code", "unknown")
            if ((state == "completed" and code != "0") or
                    (state == "failed" and (not re.fullmatch(r"-?\d+", code) or int(code) == 0)) or
                    (state == "interrupted" and code != "unknown" and not re.fullmatch(r"-?\d+", code))):
                issue("invalid_run_exit", run_path, "运行状态与实际退出码不一致")
            if not present(section_content(run_body, "Observations")):
                issue("missing_run_observations", run_path, "终态运行需记录观测或失败原因")
            if state == "completed" and not present(section_content(run_body, "Metrics")):
                issue("missing_run_metrics", run_path, "已完成运行缺少实测指标")
            if state != "completed" and not present(section_content(run_body, "Limitations")):
                issue("missing_run_limitations", run_path, "失败/中断需说明限制及缺失结果")
            artifacts = table_rows(run_body, "Artifacts")
            if not artifacts:
                unavailable = data.get("artifacts_status") == "unavailable" and present(section_content(run_body, "Limitations"))
                issue("missing_run_artifacts", run_path, "没有可核验产物", "P3" if unavailable and state != "completed" else "P2")
            for row in artifacts:
                if len(row) != 3 or not HASH.fullmatch(row[1]) or not present(row[2]):
                    issue("invalid_artifact_manifest", run_path, "产物表需有 Path、SHA256、Purpose")
                    continue
                location, expected, _ = row
                try:
                    uri = urlsplit(location)
                except ValueError as exc:
                    issue("invalid_artifact_uri", run_path, str(exc))
                    continue
                if uri.scheme in {"https", "s3", "gs"}:
                    if not uri.netloc:
                        issue("invalid_artifact_uri", run_path, "外部产物 URI 缺少存储地址")
                        continue
                    issue("external_artifact_unverified", run_path, f"未自动核验外部产物: {location}", "P3")
                    continue
                try:
                    artifact = within(workspace.parent, location)
                    if not artifact.is_file():
                        raise SpecError(f"产物不存在: {location}")
                    if verify_artifacts and digest_file(artifact) != expected:
                        raise SpecError(f"产物校验值不符: {location}")
                except (OSError, SpecError) as exc:
                    issue("invalid_run_artifact", run_path, str(exc))
            patch = data.get("patch", "none")
            if patch != "none" and patch not in {row[0] for row in artifacts if row}:
                issue("missing_run_patch", run_path, "未提交补丁需登记在 Artifacts 表")

        reviewed_coverage = []
        reviewed_results = {}
        conclusions = {path.stem: path for path in (directory / "conclusions").glob("*.md")}
        for cid, conclusion_path in sorted(conclusions.items()):
            record = read(conclusion_path)
            if record is None:
                continue
            data, conclusion_body = record
            if data.get("experiment_id") != experiment_id or data.get("conclusion_id") != cid:
                issue("invalid_conclusion_id", conclusion_path, "结论身份与路径不一致")
            if data.get("status") not in {"draft", "reviewed"}:
                issue("invalid_conclusion_status", conclusion_path, "未知结论状态")
            supersedes = data.get("supersedes", "none")
            if supersedes != "none" and (supersedes not in conclusions or supersedes == cid):
                issue("invalid_conclusion_supersedes", conclusion_path, "被替代结论不存在或自引用")
            rows = table_rows(conclusion_body, "Run Evidence")
            covered = set()
            valid = True
            stale = False
            for row in rows:
                if len(row) != 3 or row[0] not in runs or row[0] in covered or not HASH.fullmatch(row[1]):
                    issue("invalid_conclusion_run", conclusion_path, "运行引用不存在、重复或表格式错误")
                    valid = False
                    continue
                covered.add(row[0])
                run, _, run_path = runs[row[0]]
                try:
                    snapshot = within(workspace, row[2])
                    expected_path = directory / "evidence" / row[0] / f"{row[1]}.md"
                    frozen, _ = read_record(snapshot)
                    if (snapshot != expected_path or digest_file(snapshot) != row[1]
                            or frozen.get("experiment_id") != experiment_id
                            or frozen.get("run_id") != row[0] or frozen.get("status") not in TERMINAL_RUNS):
                        raise SpecError("运行证据快照身份或校验值不匹配")
                except (OSError, UnicodeError, SpecError) as exc:
                    issue("invalid_run_snapshot", conclusion_path, str(exc))
                    valid = False
                if run.get("status") not in TERMINAL_RUNS or digest_file(run_path) != row[1]:
                    stale = True
            if data.get("status") != "reviewed":
                continue
            if not covered:
                issue("empty_conclusion_evidence", conclusion_path, "已审阅结论缺少运行证据")
                valid = False
            for heading in ("Analysis", "Limitations", "Decision Impact", "Review"):
                if not present(section_content(conclusion_body, heading)):
                    issue("incomplete_conclusion", conclusion_path, f"缺少 {heading}")
                    valid = False
            mode = data.get("review_mode")
            if (not present(data.get("author")) or not present(data.get("reviewer"))
                    or mode not in {"independent", "self"}
                    or mode == "independent" and data.get("author") == data.get("reviewer")):
                issue("invalid_experiment_reviewer", conclusion_path, "审阅身份/模式无效，不能冒充独立审核")
                valid = False
            if data.get("decision") not in {"adopt", "reject", "inconclusive"}:
                issue("missing_experiment_decision", conclusion_path, "缺少明确决策")
                valid = False
            try:
                review_path = within(workspace.parent, data.get("review_evidence", "none"))
                review, review_body = read_record(review_path)
                expected = {"experiment_id": experiment_id, "conclusion_id": cid,
                            "conclusion_sha256": conclusion_digest(data, conclusion_body),
                            "reviewer": data.get("reviewer"), "review_mode": mode, "verdict": "pass"}
                if (any(review.get(key) != value for key, value in expected.items())
                        or not present(section_content(review_body, "Findings"))
                        or not present(section_content(review_body, "Assessment"))):
                    raise SpecError("审核记录与结论内容/身份不匹配")
            except (OSError, UnicodeError, SpecError) as exc:
                issue("invalid_experiment_review", conclusion_path, str(exc))
                valid = False
            reviewed_results[cid] = (valid, stale, covered, supersedes)
        superseded = set()
        for cid, result in reviewed_results.items():
            if not result[0] or result[1]:
                continue
            prior, seen = result[3], {cid}
            while prior in reviewed_results and reviewed_results[prior][0] and prior not in seen:
                superseded.add(prior)
                seen.add(prior)
                prior = reviewed_results[prior][3]
        for cid, (valid, stale, covered, supersedes) in reviewed_results.items():
            seen = {cid}
            prior = supersedes
            while prior in reviewed_results:
                if prior in seen:
                    issue("conclusion_supersedes_cycle", conclusions[cid], "结论替代关系存在环")
                    valid = False
                    break
                seen.add(prior)
                prior = reviewed_results[prior][3]
            if cid not in superseded:
                if stale:
                    issue("stale_conclusion_evidence", conclusions[cid], "当前运行已变更，需新结论替代旧结论")
                elif valid:
                    reviewed_coverage.append(covered)
        unfinished = any(data.get("status") not in TERMINAL_RUNS for data, _, _ in runs.values())
        if status in {"completed", "cancelled"} and unfinished:
            issue("unfinished_experiment_run", plan_path, "实验结束前仍有未终止的运行")
        if status == "completed" and (not runs or set(runs) not in reviewed_coverage):
            issue("missing_experiment_conclusion", plan_path, "结束实验须有覆盖当前全部运行的已审阅结论")
        if meta.get("archived", "false") == "true":
            summary["archived"].append(experiment_id)
            if status not in {"completed", "cancelled"} or unfinished:
                issue("invalid_experiment_archive", plan_path, "进行中的实验不能归档")
            if not present(meta.get("archived_at")) or not present(meta.get("archive_reason")):
                issue("incomplete_experiment_archive", plan_path, "归档需时间与原因")
    summary["run_states"] = dict(run_states)
    return summary, findings
