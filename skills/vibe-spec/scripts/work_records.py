"""Append-only work records and shared, fail-fast per-record locks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

from vibe_spec_core import SpecError, atomic_write_many, workspace_path


def contained_path(workspace: Path, record: Path) -> Path:
    """Resolve aliases, including nonexistent leaves, without leaving workspace."""
    root = workspace.resolve(strict=True)
    if not root.is_dir():
        raise SpecError("workspace must be an existing directory")
    try:
        path = (record if record.is_absolute() else root / record).resolve()
        path.relative_to(root)
    except (ValueError, RuntimeError) as exc:
        raise SpecError("record must stay inside workspace") from exc
    if path == root:
        raise SpecError("record must name a file inside workspace")
    return path


@contextmanager
def record_lock(workspace: Path, record: Path) -> Iterator[None]:
    """Lock a normalized workspace-relative path; the record need not exist.

    All cooperating writers must acquire this lock before reading or creating a
    record. Locks are non-reentrant and never waited on. After a process crash,
    remove a stale lock only after checking its recorded PID and owner process.
    """
    path = contained_path(workspace, record)
    root = workspace.resolve(strict=True)
    relative = path.relative_to(root).as_posix()
    directory = root / ".locks"
    if directory.is_symlink():
        raise SpecError("lock directory must not be a symlink")
    directory.mkdir(exist_ok=True)
    key = hashlib.sha256(relative.encode("utf-8")).hexdigest()
    lock = directory / f"{key}.lock"
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise SpecError(f"record is locked: {relative}; retry after the writer finishes") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"pid": os.getpid(), "record": relative}, handle)
        yield
    finally:
        lock.unlink(missing_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def history_path(workspace: Path, kind: str) -> Path:
    if kind not in {"handoffs", "events"}:
        raise SpecError("unknown history kind")
    for path in (workspace / "history", workspace / "history" / kind):
        if path.is_symlink():
            raise SpecError("history directories must not be symlinks")
    prefix = utc_now().replace(":", "").replace("-", "") + "-" if kind == "handoffs" else ""
    return contained_path(workspace, Path("history") / kind / f"{prefix}{uuid.uuid4()}.md")


def write_record_with_history(
    workspace: Path, record: Path, text: str, history: Path, history_text: str
) -> None:
    """Caller holds record_lock; history is immutable and committed with record."""
    with record_lock(workspace, history):
        if history.exists() or history.is_symlink():
            raise SpecError(f"history already exists: {history.name}")
        # History goes first: a failed final replacement removes it on rollback,
        # while leaving the original record untouched.
        atomic_write_many({history: history_text, record: text})


def read_record(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def resolve_record(workspace: Path, record: str) -> Path:
    relative = Path(record)
    if (not record or relative.is_absolute() or ".." in relative.parts
            or "\\" in record or ":" in record or "\x00" in record):
        raise SpecError("RECORD must be a relative Markdown path inside .vibe-spec")
    path = contained_path(workspace, relative)
    for candidate in (relative, path.relative_to(workspace.resolve())):
        if any(part.lower() in {"history", "templates", ".locks"} for part in candidate.parts):
            raise SpecError("templates, history and lock records are read-only")
        if len(candidate.parts) >= 3 and candidate.parts[0] == "experiments" and candidate.parts[2] in {"plans", "evidence"}:
            raise SpecError("experiment evidence snapshots are read-only")
    if path.suffix.lower() != ".md" or not path.is_file():
        raise SpecError("RECORD must name an existing Markdown file")
    return path


def append_progress(text: str, entry: str) -> str:
    """Insert without rewriting old text, ignoring headings inside code fences."""
    offset = 0
    progress = False
    fence = ""
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + ",}", stripped):
                fence = ""
        elif marker:
            fence = marker.group(1)
        elif re.fullmatch(r"##[ \t]+Progress[ \t]*", stripped):
            progress = True
        elif progress and re.match(r"^#{1,2}[ \t]+", line):
            return text[:offset] + "\n" + entry + "\n\n" + text[offset:]
        offset += len(line)
    separator = "\n" if text.endswith("\n") else "\n\n"
    return text + separator + ("" if progress else "## Progress\n\n") + entry + "\n"


def _inline(text: str) -> str:
    return " ".join(text.split()).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def record_work(
    target: Path, record: str, actor: str, event: str, summary: str,
    evidence: list[str] | None = None, next_action: str | None = None,
) -> tuple[Path, Path]:
    if not all(value.strip() for value in (actor, event, summary)):
        raise SpecError("actor, event and summary must not be empty")
    workspace = workspace_path(target)
    if workspace.is_symlink():
        raise SpecError(".vibe-spec must not be a symlink")
    path = resolve_record(workspace, record)
    with record_lock(workspace, path):
        history = history_path(workspace, "events")
        timestamp = utc_now()
        entry = (f"- {timestamp} | {_inline(actor)} | {_inline(event)}: {_inline(summary)} "
                 f"([record {history.stem}]({quote(os.path.relpath(history, path.parent))}))")
        if next_action:
            entry += f"; next: {_inline(next_action)}"
        details = (f"# Work Event {history.stem}\n\n"
                   f"- Time: {timestamp}\n- Actor: {_inline(actor)}\n- Event: {_inline(event)}\n"
                   f"- Record: [{_inline(path.relative_to(workspace.resolve()).as_posix())}]"
                   f"({quote(os.path.relpath(path, history.parent))})\n\n"
                   f"## Summary\n\n{summary}\n\n## Evidence\n\n")
        details += "\n\n".join(evidence or ["none"]) + "\n\n## Next Action\n\n"
        details += (next_action or "none") + "\n"
        write_record_with_history(workspace, path, append_progress(read_record(path), entry), history, details)
    return path, history
