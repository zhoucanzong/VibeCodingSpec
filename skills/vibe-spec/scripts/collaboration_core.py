"""只读检查协作记录；通信和工程验收由当前 Agent 执行。"""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath

from vibe_spec_core import SpecError, has_verification_evidence, meaningful, parse_frontmatter, section_content


TASK_STATES = {"draft", "assigned", "running", "blocked", "submitted", "accepted", "cancelled"}
OCCUPIED = {"assigned", "running", "blocked", "submitted"}


def inspect_collaboration(workspace: Path) -> tuple[dict, list[dict]]:
    root = workspace / "collaboration"
    findings: list[dict] = []

    def issue(code: str, path: Path, message: str) -> None:
        findings.append({"severity": "P2", "code": code,
                         "location": str(path.relative_to(workspace)), "message": message})

    def read(path: Path) -> tuple[dict, str] | None:
        try:
            if not path.resolve().is_relative_to(root.resolve()):
                raise SpecError("协作记录不能指向目录外")
            data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            if any(isinstance(value, list) and key not in {"depends_on", "write_scope"}
                   for key, value in data.items()):
                raise SpecError("仅 depends_on/write_scope 可使用列表值")
            return data, body
        except (OSError, UnicodeError, SpecError) as exc:
            issue("invalid_collaboration_record", path, str(exc))
            return None

    def records(directory: str, key: str) -> dict:
        result = {}
        for path in sorted((root / directory).glob("*.md")):
            parsed = read(path)
            if parsed is None:
                continue
            data, body = parsed
            identifier = data.get(key)
            if not isinstance(identifier, str) or identifier != path.stem or not meaningful(identifier):
                issue("invalid_collaboration_id", path, f"{key} 必须与文件名一致且非占位符")
                continue
            result[identifier] = (data, body, path)
        return result

    def present(value: object) -> bool:
        return isinstance(value, str) and value not in {"unknown", "none", "latest"} and meaningful(value)

    team = read(root / "TEAM.md")
    agents = records("agents", "agent_id")
    tasks = records("tasks", "task_id")
    messages = records("messages", "message_id")
    coordinator = team[0].get("coordinator") if team else None
    revision = team[0].get("rules_revision") if team else None
    if not isinstance(coordinator, str) or coordinator not in agents:
        issue("missing_coordinator", root / "TEAM.md", "主管尚未登记")
    elif agents[coordinator][0].get("role") != "coordinator":
        issue("invalid_coordinator", root / "TEAM.md", "主管角色必须为 coordinator")
    if not present(revision):
        issue("missing_rules_revision", root / "TEAM.md", "需记录明确规范版本")

    def receipt(value: object, expected: dict, path: Path, code: str) -> None:
        matched = None
        if isinstance(value, str):
            for data, body, message_path in messages.values():
                if value == message_path.relative_to(workspace).as_posix():
                    matched = (data, body)
                    break
        if matched is None or not meaningful(matched[1]) or any(
            matched[0].get(key) != val for key, val in expected.items()
        ):
            issue(code, path, "缺少与身份、消息及当前版本匹配的真实回执记录")

    for identifier, (data, _, path) in agents.items():
        role, state = data.get("role"), data.get("status")
        if role not in {"coordinator", "lead", "worker", "reviewer"}:
            issue("invalid_agent_role", path, "未知成员角色")
        if role == "coordinator" and identifier != coordinator:
            issue("multiple_coordinators", path, "当前只能有一位主管，交接后更新角色")
        if state not in {"local", "invited", "connected", "blocked", "disconnected"}:
            issue("invalid_agent_status", path, "未知连接状态")
        if state == "local" and (identifier != coordinator or data.get("transport") != "self"):
            issue("invalid_local_agent", path, "local/self 仅用于当前主管")
        if state in {"connected", "local"} and data.get("rules_revision") != revision:
            issue("agent_rules_drift", path, "成员尚未确认当前规范版本")
        if state == "connected":
            if data.get("transport") not in {"native", "cli", "mailbox", "manual"}:
                issue("invalid_transport", path, "未知通信通道")
            if not all(present(data.get(key)) for key in ("endpoint", "workspace", "hello_message")):
                issue("missing_agent_endpoint", path, "已连接成员缺少地址、目录或握手消息 ID")
            receipt(data.get("hello_ack"), {"kind": "hello_ack", "sender": identifier,
                    "recipient": coordinator, "reply_to": data.get("hello_message"),
                    "revision": revision, "endpoint": data.get("endpoint")},
                    path, "missing_hello_ack")

    for data, _, path in messages.values():
        if any(not isinstance(data.get(key), str) or data.get(key) not in agents
               for key in ("sender", "recipient")):
            issue("unknown_message_agent", path, "消息收发方必须为登记成员")

    spec_ids = set()
    for path in (workspace / "specs").glob("*.md"):
        try:
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if isinstance(meta.get("spec_id"), str):
                spec_ids.add(meta["spec_id"])
        except (OSError, UnicodeError, SpecError):
            pass  # 主检查器负责报告 spec 文件格式问题。

    scopes = {}
    dependencies = {}
    for identifier, (data, body, path) in tasks.items():
        state = data.get("status")
        if state not in TASK_STATES:
            issue("invalid_task_status", path, "未知任务状态")
        execution = data.get("execution_state", "unknown")
        if execution not in {"unknown", "not_started", "may_be_running", "stopped"}:
            issue("invalid_execution_state", path, "未知执行状态")
        if execution == "not_started" and state in {"running", "submitted", "accepted"}:
            issue("invalid_execution_state", path, "运行或交付后不能声明从未开始执行")
        raw_deps = data.get("depends_on", [])
        deps = raw_deps if isinstance(raw_deps, list) else []
        dependencies[identifier] = deps
        if not isinstance(raw_deps, list) or any(dep not in tasks or dep == identifier for dep in deps):
            issue("invalid_task_dependency", path, "依赖必须是存在的其他任务 ID 列表")
        raw_scope = data.get("write_scope", [])
        scope = raw_scope if isinstance(raw_scope, list) else []
        if not isinstance(raw_scope, list) or any(
            PurePosixPath(item).is_absolute() or ".." in PurePosixPath(item).parts
            or any(char in item for char in "*?[]\\") or not item for item in scope
        ):
            issue("invalid_write_scope", path, "write_scope 必须为仓库相对路径列表，不含 ..、glob 或反斜杠")
        scopes[identifier] = [PurePosixPath(item) for item in scope]
        if state in {"draft", "cancelled"}:
            continue
        for field in ("owner", "acceptor"):
            member = data.get(field)
            if not isinstance(member, str) or member not in agents:
                issue("unknown_task_agent", path, f"{field} 未登记")
            elif state in {"assigned", "running", "submitted"} and agents[member][0].get("status") not in {"local", "connected"}:
                issue("unconnected_task_agent", path, f"{field} 尚未连接")
        if data.get("owner") == data.get("acceptor"):
            issue("self_acceptance", path, "任务不能由执行者自行验收")
        if not isinstance(data.get("spec_id"), str) or data.get("spec_id") not in spec_ids:
            issue("unknown_task_spec", path, "任务必须关联实际 Spec")
        if data.get("rules_revision") != revision and state != "accepted":
            issue("task_rules_drift", path, "任务依据与当前规范不同，请同步后继续")
        for field in ("stream", "base_revision", "workspace"):
            if not present(data.get(field)):
                issue("incomplete_task", path, f"缺少 {field}")
        for heading in ("Goal", "Acceptance Criteria"):
            if not present(section_content(body, heading)):
                issue("incomplete_task", path, f"缺少 {heading}")
        if state in {"running", "submitted", "accepted"} and any(
            dep not in tasks or tasks[dep][0].get("status") != "accepted" for dep in deps
        ):
            issue("unfinished_dependency", path, "前置任务尚未验收")
        if state in {"submitted", "accepted"}:
            if not present(data.get("deliverable_revision")) or any(
                not present(section_content(body, heading)) for heading in ("Verification", "Result")
            ):
                issue("missing_task_evidence", path, "提交交付须有版本、验证与结果")
        if state == "accepted":
            if not has_verification_evidence(section_content(body, "Verification") or ""):
                issue("missing_task_verification", path, "已验收任务缺少结构化 PASS 验证证据")
            receipt(data.get("acceptance"), {"kind": "acceptance", "sender": data.get("acceptor"),
                    "recipient": data.get("owner"), "task_id": identifier,
                    "revision": data.get("deliverable_revision"),
                    "rules_revision": data.get("rules_revision"), "verdict": "pass"},
                    path, "missing_task_acceptance")

    # 沿依赖链检测环；不把 DAG 的共同祖先误报为环。
    def cyclic(identifier: str, stack: set[str], done: set[str]) -> bool:
        if identifier in stack:
            return True
        if identifier in done:
            return False
        if any(cyclic(dep, stack | {identifier}, done) for dep in dependencies.get(identifier, [])):
            return True
        done.add(identifier)
        return False

    if any(cyclic(identifier, set(), set()) for identifier in tasks):
        issue("task_dependency_cycle", root / "TEAM.md", "任务依赖存在环，需主管调整")
    occupied = [(key, record) for key, record in tasks.items()
                if record[0].get("status") in OCCUPIED
                and not (record[0].get("status") == "blocked"
                         and record[0].get("execution_state") == "not_started")]
    for index, (left, (_, _, path)) in enumerate(occupied):
        for right, _ in occupied[index + 1:]:
            if any(a == b or a in b.parents or b in a.parents for a in scopes[left] for b in scopes[right]):
                issue("overlapping_write_scope", path, f"与任务 {right} 修改范围重叠，需串行或重新划分")

    summary = {"coordinator": coordinator, "rules_revision": revision,
               "agents": {key: value[0].get("status") for key, value in agents.items()},
               "tasks": dict(Counter(str(value[0].get("status")) for value in tasks.values())),
               "blocked_tasks": [key for key, value in tasks.items() if value[0].get("status") == "blocked"]}
    return summary, findings
