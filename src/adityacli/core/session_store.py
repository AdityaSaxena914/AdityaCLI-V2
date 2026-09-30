from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from adityacli.core.models import Message, Role


type JSONValue = (
    None
    | bool
    | int
    | float
    | str
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)

type JSONObject = dict[str, JSONValue]


class SessionStore:
    """
    Deterministic persistence for the active session.

    Stores only what's actually read back: session metadata and the
    conversation transcript. Nothing here tracks statistics or caches
    file content that nothing consumes.
    """

    def __init__(self, workspace: Path) -> None:
        self._root: Path = workspace / ".sessions" / "current"
        self._session: Path = self._root / "session.json"
        self._chat: Path = self._root / "chat.jsonl"
        self._memory: Path = self._root / "memory.json"

    @property
    def exists(self) -> bool:
        return self._root.exists()

    def create(self, model: str, context_window: int) -> None:
        """
        Create a fresh session.
        """

        self._root.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC).isoformat()

        self._write_json(
            self._session,
            {
                "id": now,
                "created_at": now,
                "updated_at": now,
                "model": model,
                "context_window": context_window,
            },
        )

        with self._chat.open("w", encoding="utf-8"):
            pass

    def load_messages(self) -> list[Message]:
        """
        Load the persisted conversation.
        """

        if not self._chat.exists():
            return []

        messages: list[Message] = []

        for line in self._chat.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue

            obj = cast(dict[str, str], cast(object, json.loads(line)))

            messages.append(
                Message(
                    role=Role(obj["role"]),
                    content=obj["content"],
                )
            )

        return messages

    def append_message(self, message: Message) -> None:
        """
        Persist one message.
        """

        record = {
            "role": message.role.value,
            "content": message.content,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        with self._chat.open("a", encoding="utf-8") as file:
            _ = file.write(json.dumps(record))
            _ = file.write("\n")

    def read_memory(self) -> dict[str, str]:
        """
        Load previously-read file contents (path -> content), so a
        follow-up question in a resumed session can still refer to
        files read earlier without re-reading them.
        """

        if not self._memory.exists():
            return {}

        raw = cast(
            dict[str, str],
            cast(object, json.loads(self._memory.read_text(encoding="utf-8"))),
        )

        return raw

    def write_read_memory(self, files: dict[str, str]) -> None:
        self._write_json(self._memory, cast(JSONObject, files))

    def clear(self, model: str, context_window: int) -> None:
        if self._root.exists():
            shutil.rmtree(self._root)

        self.create(model=model, context_window=context_window)

    @staticmethod
    def _write_json(path: Path, data: JSONObject) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=path.name,
            suffix=".tmp",
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)
