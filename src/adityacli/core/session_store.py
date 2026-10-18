from __future__ import annotations

import json
import os
import shutil
import tempfile
import re
import uuid
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from adityacli.core.models import Message, Role
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import ValidationError
from adityacli.core.locking import file_lock


class SessionStore:
    """Append-only memory journal, with migration from the legacy files."""

    def __init__(self, workspace: Path) -> None:
        self._guard = WorkspaceGuard(workspace)

    def _path(self, name: str = "") -> Path:
        return self._guard.resolve(f".sessions/current/{name}")

    @contextmanager
    def transaction(self):
        lock = self._guard.resolve(".sessions/store.lock")
        with file_lock(lock):
            self._recover_reset()
            yield

    def workspace_lease(self):
        """CLI lifetime ownership; a second process cannot reset this session."""
        return file_lock(self._guard.resolve(".sessions/owner.lock"), timeout=0)

    def _remove_tree(self, relative: str) -> None:
        target = self._guard.resolve(relative)
        if target.exists():
            shutil.rmtree(target)

    def _recover_reset(self) -> None:
        marker = self._guard.resolve(".sessions/reset.json")
        if not marker.exists():
            return
        try:
            intent = json.loads(self._guard.read_text(".sessions/reset.json"))
            stage, backup = intent["stage"], intent["backup"]
            if not re.fullmatch(r"\.new-[0-9a-f]{32}", stage) or not re.fullmatch(r"\.old-[0-9a-f]{32}", backup):
                raise ValueError("Invalid reset directory")
        except (ValueError, KeyError, TypeError) as exc:
            raise ValidationError("Session reset recovery record is invalid.") from exc
        previous = self._guard.resolve(f".sessions/{backup}")
        prepared = self._guard.resolve(f".sessions/{stage}")
        current = self._path()
        if not current.exists():
            if previous.exists():
                os.replace(previous, current)  # Interrupted before commit: restore.
            elif prepared.exists():
                os.replace(prepared, current)  # Initial creation had no old state.
            else:
                raise ValidationError("Session reset cannot recover its previous state.")
        # A present current directory is the committed session, or the old
        # directory when interruption preceded the first rename.
        try:
            self._remove_tree(f".sessions/{backup}")
            self._remove_tree(f".sessions/{stage}")
            marker.unlink()
        except OSError:
            # Warning filters must not turn a committed reset into an apparent
            # failure with stale in-memory state.
            try:
                warnings.warn("Session is usable; old reset files await cleanup.", RuntimeWarning)
            except RuntimeWarning:
                pass

    @property
    def exists(self) -> bool:
        with self.transaction():
            return self._path().exists()

    def create(self, model: str, context_window: int, *, initial_messages: list[Message] | None = None) -> None:
        with self.transaction():
            marker = self._guard.resolve(".sessions/reset.json")
            if marker.exists():
                raise ValidationError("Previous session reset cleanup is pending; retry after storage is available.")
            token = uuid.uuid4().hex
            stage, backup = f".new-{token}", f".old-{token}"
            prepared = self._guard.resolve(f".sessions/{stage}")
            prepared.mkdir()
            committed = False
            try:
                now = datetime.now(UTC).isoformat()
                self._write_json(prepared / "session.json", {
                    "id": now, "created_at": now, "updated_at": now,
                    "model": model, "context_window": context_window, "version": 1,
                })
                with (prepared / "memory.jsonl").open("wb") as journal:
                    for message in initial_messages or []:
                        record = {"v": 1, "type": "message", "role": message.role.value,
                                  "content": message.content, "context": True}
                        self._validate_record(record)
                        journal.write((json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
                    journal.flush()
                    os.fsync(journal.fileno())
                self._write_json(marker, {"stage": stage, "backup": backup})
                current = self._path()
                if current.exists():
                    os.replace(current, self._guard.resolve(f".sessions/{backup}"))
                os.replace(prepared, current)
                committed = True
            except BaseException:
                if marker.exists():
                    self._recover_reset()
                raise
            finally:
                if committed:
                    # Cleanup is after the commit point. Do not report the old
                    # state on failure: recovery retries cleanup on the next access.
                    self._recover_reset()
                elif prepared.exists() and not marker.exists():
                    self._remove_tree(f".sessions/{stage}")

    def _ensure_journal(self) -> Path:
        journal = self._path("memory.jsonl")
        if journal.exists():
            return journal
        self._path().mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self._path(), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as destination:
                chat = self._path("chat.jsonl")
                if chat.exists():
                    with chat.open(encoding="utf-8") as source:
                        for line in source:
                            if line.strip():
                                record = json.loads(line)
                                record["type"] = "message"
                                content = record.get("content", "")
                                if record.get("role") == "user" and "\n" not in content and content.split(maxsplit=1)[0:1] in (["/read"], ["/search"], ["/git"]):
                                    record["context"] = False
                                destination.write(json.dumps(record, ensure_ascii=False) + "\n")
                memory = self._path("memory.json")
                if memory.exists():
                    with memory.open(encoding="utf-8") as source:
                        for path, content in json.load(source).items():
                            self._guard.resolve(path)
                            destination.write(json.dumps({"type": "file", "path": path, "content": content}, ensure_ascii=False) + "\n")
                destination.flush()
                os.fsync(destination.fileno())
            self._path("memory.jsonl")
            os.replace(temporary, journal)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        return journal

    def _records(self) -> Iterator[dict]:
        with self.transaction(), self._ensure_journal().open("rb") as file:
            for number, line in enumerate(file, 1):
                if line.strip():
                    try:
                        record = json.loads(line)
                    except (ValueError, UnicodeError) as exc:
                        if not line.endswith(b"\n"):
                            # A crash can interrupt only the final append.
                            return
                        raise ValidationError(f"Session journal is corrupted at line {number}.") from exc
                    self._validate_record(record, number)
                    if record.get("type") == "batch":
                        yield from record["records"]
                    else:
                        yield record

    def _validate_record(self, record: dict, line: int = 0) -> None:
        try:
            if not isinstance(record, dict) or type(record.get("v", 1)) is not int or record.get("v", 1) != 1:
                raise ValueError("Unsupported record version")
            kind = record.get("type", "message")
            if kind == "batch":
                records = record["records"]
                if not isinstance(records, list) or not records:
                    raise ValueError("Invalid operation batch")
                for item in records:
                    if not isinstance(item, dict) or item.get("type") == "batch":
                        raise ValueError("Nested operation batches are unsupported")
                    self._validate_record(item, line)
            elif kind == "message":
                Role(record["role"])
                if not isinstance(record["content"], str) or type(record.get("context", True)) is not bool:
                    raise ValueError("Invalid message fields")
            elif kind in {"file", "forget_file", "touch_file"}:
                self.canonical_file_path(record["path"])
                if kind == "file" and not isinstance(record["content"], str):
                    raise ValueError("Invalid cached contents")
            else:
                raise ValueError("Unknown record type")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid session record at line {line}: {exc}") from exc

    def canonical_file_path(self, path: str) -> str:
        return self._guard.relative_path(path)

    def load_messages(self) -> list[Message]:
        return [
            Message(Role(record["role"]), record["content"])
            for record in self._records() if record.get("type", "message") == "message"
        ]

    def append_message(self, message: Message, *, context: bool = True) -> None:
        self._append({
            "type": "message", "role": message.role.value, "content": message.content,
            "context": context, "timestamp": datetime.now(UTC).isoformat(),
        })

    def load_context_messages(self) -> list[Message]:
        return [
            Message(Role(record["role"]), record["content"])
            for record in self._records()
            if record.get("type", "message") == "message" and record.get("context", True)
        ]

    def read_memory(self) -> dict[str, str]:
        return self.load_state(context_only=True)[1]

    def load_state(self, *, context_only: bool = False) -> tuple[list[Message], dict[str, str]]:
        """Replay messages and file updates in one streaming pass."""
        messages: list[Message] = []
        files: dict[str, str] = {}
        for record in self._records():
            if record.get("type", "message") == "message":
                if not context_only or record.get("context", True):
                    messages.append(Message(Role(record["role"]), record["content"]))
            elif record.get("type") == "file":
                path = self.canonical_file_path(record["path"])
                files.pop(path, None)
                files[path] = record["content"]
            elif record.get("type") == "forget_file":
                files.pop(self.canonical_file_path(record["path"]), None)
            elif record.get("type") == "touch_file":
                path = self.canonical_file_path(record["path"])
                if path in files:
                    files[path] = files.pop(path)
        return messages, files

    def cache_file(self, path: str, content: str) -> None:
        path = self.canonical_file_path(path)
        self._append({"type": "file", "path": path, "content": content})

    def forget_file(self, path: str) -> None:
        self._append({"type": "forget_file", "path": path})

    def touch_file(self, path: str) -> None:
        self._append({"type": "touch_file", "path": path})

    def _append(self, record: dict) -> None:
        self.append_records([record])

    def append_records(self, records: list[dict]) -> None:
        """Commit one logical operation, including cache eviction, under one lock."""
        for record in records:
            self._validate_record(record)
        if not records:
            return
        # One line is the crash boundary: eviction plus insertion cannot replay
        # partially after an interrupted append.
        operation = records[0] if len(records) == 1 else {"type": "batch", "records": records}
        data = (json.dumps({"v": 1, **operation}, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        with self.transaction(), self._ensure_journal().open("r+b") as file:
            file.seek(0, os.SEEK_END)
            end = file.tell()
            if end:
                file.seek(end - 1)
                if file.read(1) != b"\n":
                    # Locate only the unfinished final record, without
                    # reading or rewriting the complete session archive.
                    start = end
                    while start:
                        offset = max(0, start - 4096)
                        file.seek(offset)
                        chunk = file.read(start - offset)
                        newline = chunk.rfind(b"\n")
                        start = offset + newline + 1 if newline >= 0 else offset
                        if newline >= 0:
                            break
                    file.seek(start)
                    tail = file.read()
                    try:
                        json.loads(tail)
                    except (ValueError, UnicodeError):
                        file.seek(start)
                        file.truncate()
                    else:
                        file.write(b"\n")
            file.seek(0, os.SEEK_END)
            start = file.tell()
            try:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            except BaseException:
                file.seek(start)
                file.truncate()
                file.flush()
                raise

    def clear(self, model: str, context_window: int, *, initial_messages: list[Message] | None = None) -> None:
        if initial_messages is None:
            self.create(model=model, context_window=context_window)
        else:
            self.create(model=model, context_window=context_window, initial_messages=initial_messages)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
