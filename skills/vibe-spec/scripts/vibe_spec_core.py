#!/usr/bin/env python3
"""vibe-spec 脚本共享的受控 Markdown 和生命周期工具。"""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


VALID_STATES = {
    "idea",
    "draft",
    "ready_for_review",
    "approved",
    "in_progress",
    "implemented",
    "verification_failed",
    "verified",
    "reviewed",
    "active",
    "needs_update",
    "needs_sync",
    "needs_changes",
    "superseded",
    "deprecated",
    "archived",
}

TRANSITIONS = {
    "idea": {"draft", "archived"},
    "draft": {"ready_for_review", "archived"},
    "ready_for_review": {"draft", "approved", "needs_changes"},
    "approved": {"in_progress", "needs_update", "archived"},
    "in_progress": {"implemented", "needs_update", "archived"},
    "implemented": {"verified", "verification_failed", "needs_changes"},
    "verification_failed": {"in_progress", "archived"},
    "verified": {"reviewed", "needs_changes", "in_progress"},
    "reviewed": {"active", "needs_changes", "in_progress"},
    "active": {"needs_update", "needs_sync", "superseded", "deprecated"},
    "needs_update": {"draft", "archived"},
    "needs_sync": {"draft", "archived"},
    "needs_changes": {"draft", "in_progress", "archived"},
    "superseded": {"archived"},
    "deprecated": {"archived"},
    "archived": set(),
}

REQUIRED_SPEC_SECTIONS = (
    "Summary",
    "Context",
    "Goals",
    "Non-Goals",
    "Inherits From",
    "Adds",
    "Overrides",
    "Requirements",
    "Acceptance Criteria",
    "Implementation Notes",
    "Verification Plan",
    "Review Notes",
    "Lifecycle Log",
    "Changelog",
)


class SpecError(RuntimeError):
    """表示确定性的 spec 工作区错误。"""


@dataclass
class CommandResult:
    ok: bool
    command: str
    changes: list[Any] = field(default_factory=list)
    findings: list[Any] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


@dataclass
class SpecDocument:
    path: Path
    metadata: dict[str, Any]
    body: str

    @property
    def spec_id(self) -> str:
        return str(self.metadata.get("spec_id", ""))

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", ""))

    @property
    def text(self) -> str:
        return render_frontmatter(self.metadata) + self.body.lstrip("\n")


def workspace_path(target: Path | str) -> Path:
    target_path = Path(target).expanduser().resolve()
    if target_path.name == ".vibe-spec":
        return target_path
    return target_path / ".vibe-spec"


def parse_value(raw: str) -> Any:
    value = raw.strip().strip('"').strip("'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise SpecError("spec 缺少 YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker == -1:
        raise SpecError("spec frontmatter 未闭合")
    metadata: dict[str, Any] = {}
    for line in text[4:marker].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise SpecError(f"无法解析 frontmatter 行: {line}")
        key, raw = line.split(":", 1)
        metadata[key.strip()] = parse_value(raw)
    return metadata, text[marker + 5 :]


def render_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def render_frontmatter(metadata: dict[str, Any]) -> str:
    preferred = [
        "spec_id",
        "status",
        "parent",
        "extends",
        "supersedes",
        "created",
        "updated",
        "owner_agent",
    ]
    keys = [key for key in preferred if key in metadata]
    keys.extend(sorted(key for key in metadata if key not in keys))
    lines = ["---"]
    lines.extend(f"{key}: {render_value(metadata[key])}" for key in keys)
    lines.extend(["---", ""])
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        Path(temp_name).replace(path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def atomic_write_many(files: dict[Path, str]) -> None:
    """先预写全部临时文件，再替换目标，避免预检失败造成半更新。"""
    staged: dict[Path, Path] = {}
    originals = {path: path.read_text(encoding="utf-8") if path.exists() else None for path in files}
    try:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
            staged[path] = Path(temp_name)
        replaced: list[Path] = []
        try:
            for path, temporary in staged.items():
                temporary.replace(path)
                replaced.append(path)
        except BaseException:
            for path in reversed(replaced):
                original = originals[path]
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, original)
            raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def load_spec(path: Path) -> SpecDocument:
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return SpecDocument(path=path, metadata=metadata, body=body)


def write_spec(spec: SpecDocument) -> None:
    atomic_write(spec.path, spec.text.rstrip() + "\n")


def section_content(text: str, heading: str) -> str | None:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return None
    next_heading = re.search(r"^## ", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end].strip()


def replace_section(text: str, heading: str, content: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    rendered = f"## {heading}\n\n{content.strip()}\n"
    if not match:
        return text.rstrip() + "\n\n" + rendered
    next_heading = re.search(r"^## ", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    suffix = text[end:].lstrip("\n")
    return text[: match.start()] + rendered + ("\n" + suffix if suffix else "")


def append_section_line(text: str, heading: str, line: str) -> str:
    current = section_content(text, heading)
    if current is None or current in {"", "TBD"}:
        return replace_section(text, heading, line)
    if line in current:
        return text
    return replace_section(text, heading, current.rstrip() + "\n" + line)


def append_lifecycle(
    text: str,
    event_date: str,
    old_state: str,
    new_state: str,
    reason: str,
    evidence: str = "none",
) -> str:
    line = (
        f"- {event_date}: `{old_state}` -> `{new_state}`; "
        f"reason: {reason}; evidence: {evidence or 'none'}"
    )
    return append_section_line(text, "Lifecycle Log", line)


def all_specs(target: Path | str) -> list[SpecDocument]:
    workspace = workspace_path(target)
    specs_dir = workspace / "specs"
    if not specs_dir.exists():
        return []
    specs = [load_spec(path) for path in sorted(specs_dir.glob("*.md"))]
    seen: dict[str, Path] = {}
    for spec in specs:
        if not spec.spec_id:
            raise SpecError(f"spec 缺少 spec_id: {spec.path}")
        if spec.spec_id in seen:
            raise SpecError(
                f"duplicate spec_id `{spec.spec_id}`: {seen[spec.spec_id]} and {spec.path}"
            )
        seen[spec.spec_id] = spec.path
    return specs


def find_spec(target: Path | str, spec_id: str) -> SpecDocument:
    matches = [spec for spec in all_specs(target) if spec.spec_id == spec_id]
    if not matches:
        raise SpecError(f"找不到 spec_id `{spec_id}`")
    return matches[0]


def next_action(status: str) -> str:
    mapping = {
        "idea": "补齐上下文并起草 spec",
        "draft": "补齐规格后推进到 ready_for_review",
        "ready_for_review": "执行规格审核",
        "approved": "开始实现",
        "in_progress": "完成实现并记录 Implementation Notes",
        "implemented": "执行验证",
        "verification_failed": "修复失败项后重新实现",
        "verified": "执行独立 review",
        "reviewed": "确认可激活",
        "active": "持续监测 drift",
        "needs_update": "更新规格",
        "needs_sync": "同步父规格和项目规则",
        "needs_changes": "修复审核问题",
        "superseded": "归档旧规格",
        "deprecated": "完成退役并归档",
        "archived": "仅保留历史",
    }
    return mapping.get(status, "检查状态")


def render_spec_index(target: Path | str, upsert: SpecDocument | None = None) -> str:
    workspace = workspace_path(target)
    specs = all_specs(target)
    if upsert is not None:
        specs = [spec for spec in specs if spec.spec_id != upsert.spec_id]
        specs.append(upsert)
    lines = [
        "# Spec 索引",
        "",
        "| Spec ID | 文件 | 状态 | 父级 | 更新时间 | 下一步 |",
        "|---|---|---|---|---|---|",
    ]
    for spec in sorted(specs, key=lambda item: item.spec_id):
        parent = str(spec.metadata.get("parent", "none"))
        updated = str(spec.metadata.get("updated", "unknown"))
        relative = spec.path.relative_to(workspace)
        lines.append(
            f"| {spec.spec_id} | `{relative}` | {spec.status} | {parent} | {updated} | {next_action(spec.status)} |"
        )
    lines.extend(
        [
            "",
            "由 vibe-spec 生命周期脚本维护。手工修改后运行 `check_vibe_spec.py --strict`。",
        ]
    )
    return "\n".join(lines) + "\n"


def rebuild_spec_index(target: Path | str) -> Path:
    workspace = workspace_path(target)
    index_path = workspace / "SPEC_INDEX.md"
    atomic_write(index_path, render_spec_index(target))
    return index_path


def meaningful(content: str | None) -> bool:
    if content is None:
        return False
    stripped = content.strip()
    placeholders = {
        "",
        "TBD",
        "unknown",
        "尚未实现。",
        "尚未审核。",
        "No implementation yet.",
        "No review yet.",
    }
    if stripped in placeholders:
        return False
    useful = [
        line.strip()
        for line in stripped.splitlines()
        if line.strip() and line.strip() not in {"- TBD", "- [ ] TBD", "- none"}
    ]
    return bool(useful)


def validate_transition(spec: SpecDocument, new_state: str) -> list[str]:
    findings: list[str] = []
    if new_state not in VALID_STATES:
        return [f"未知状态 `{new_state}`"]
    if new_state not in TRANSITIONS.get(spec.status, set()):
        return [f"不允许从 `{spec.status}` 推进到 `{new_state}`"]

    body = spec.body
    if new_state in {"ready_for_review", "approved"}:
        for heading in ("Summary", "Context", "Goals", "Requirements", "Acceptance Criteria", "Verification Plan"):
            if not meaningful(section_content(body, heading)):
                findings.append(f"门禁缺少有效章节 `{heading}`")
    if new_state == "implemented" and not meaningful(section_content(body, "Implementation Notes")):
        findings.append("门禁缺少有效章节 `Implementation Notes`")
    if new_state == "verified":
        verification = section_content(body, "Verification Plan") or ""
        if not meaningful(verification) or not has_verification_evidence(verification):
            findings.append("门禁缺少通过的验证证据")
    if new_state in {"reviewed", "active"}:
        if not review_passes_current_verification(spec):
            findings.append("门禁缺少通过的审核记录")
    return findings


def has_verification_evidence(content: str) -> bool:
    pattern = re.compile(
        r"(?im)^\s*-\s*(?:Result|结果)\s*[:：]\s*`[^`]+`\s*(?:->|:)\s*(?:PASS|PASSED|通过|成功)\b"
    )
    return bool(pattern.search(content))


def new_verification_id() -> str:
    return uuid.uuid4().hex


def review_passes_current_verification(spec: SpecDocument) -> bool:
    verification_id = str(spec.metadata.get("verification_id", ""))
    if not verification_id:
        return False
    notes = section_content(spec.body, "Review Notes") or ""
    matching = [line.strip() for line in notes.splitlines() if f"verification_id={verification_id}" in line]
    if not matching:
        return False
    latest = matching[-1]
    return "PASS" in latest and "NEEDS CHANGES" not in latest


def today() -> str:
    return date.today().isoformat()


def emit_result(result: CommandResult, as_json: bool = False) -> None:
    payload = asdict(result)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    state = "PASS" if result.ok else "FAIL"
    print(f"vibe-spec {result.command}: {state}")
    for change in result.changes:
        print(f"- changed: {change}")
    for finding in result.findings:
        print(f"- finding: {finding}")
    for action in result.next_actions:
        print(f"- next: {action}")


def command_error(command: str, message: str, as_json: bool = False) -> int:
    emit_result(
        CommandResult(False, command, findings=[message], next_actions=["根据 finding 修复后重试"]),
        as_json,
    )
    return 1
