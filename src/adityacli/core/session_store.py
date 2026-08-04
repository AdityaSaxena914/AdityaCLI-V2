from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import os
import tempfile
from adityacli.core.models import Message
from adityacli.core.token_counter import CharacterTokenCounter
import shutil

class SessionStore:
    """
    Deterministic persistence for the active session.
    """

    def __init__(self, workspace: Path) -> None:
        self._root = workspace / ".sessions" / "current"

        self._session = self._root / "session.json"
        self._index = self._root / "index.json"
        self._chat = self._root / "chat.jsonl"
        self._memory = self._root / "memory.json"
        self._cache = self._root / "cache"
        self._token_counter = CharacterTokenCounter()
        self._memory_cache: dict[str, Any] | None = None

    @property
    def exists(self) -> bool:
        return self._root.exists()

    def create(self, model: str, context_window: int) -> None:
        """
        Create a fresh session.
        """

        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

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

        self._chat.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._write_json(
            self._index,
            {
                "message_count": 0,
                "estimated_tokens": 0,
                "cached_files": 0,
            },
        )


        self._memory_cache = {
            "files": {},
        }

        self._write_json(
            self._memory,
            self._memory_cache,
        )


        with self._chat.open(
            "w",
            encoding="utf-8",
        ):
            pass

    def load_messages(self) -> list[Message]:
        """
        Load the persisted conversation.
        """

        if not self._chat.exists():
            return []

        messages: list[Message] = []

        from adityacli.core.models import Role

        for line in self._chat.read_text(
            encoding="utf-8",
        ).splitlines():
            if not line.strip():
                continue

            obj = json.loads(line)

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

        with self._chat.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(record))
            file.write("\n")

        self._append_statistics(message)

    def clear(
        self,
        model: str,
        context_window: int,
    ) -> None:
        self._memory_cache = None

        if self._root.exists():
            shutil.rmtree(self._root)

        self.create(
            model=model,
            context_window=context_window,
        )



    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

    @staticmethod
    def _write_json(
        path: Path,
        data: dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fd, temp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=path.name,
            suffix=".tmp",
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=4,
                )
                file.flush()
                os.fsync(file.fileno())

            os.replace(
                temp_name,
                path,
            )

        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)


    def cache_file(
        self,
        path: str,
        content: str,
    ) -> None:
        """
        Store or update a cached file in session memory.
        """

        memory = self._memory_data()

        files = memory.setdefault("files", {})

        now = datetime.now(UTC).isoformat()

        record = files.get(path)

        if record is None:
            files[path] = {
                "content": content,
                "sha256": self._sha256(content),
                "last_access": now,
                "access_count": 1,
            }
        else:
            record["content"] = content
            record["sha256"] = self._sha256(content)
            record["last_access"] = now
            record["access_count"] += 1


        index = self._read_json(self._index)
        index["cached_files"] = len(files)

        self._write_json(
            self._index,
            index,
        )


    def get_cached_file(
        self,
        path: str,
    ) -> str | None:
        """
        Return cached file contents if available.
        """

        memory = self._memory_data()

        record = memory["files"].get(path)

        if record is None:
            return None

        return record["content"]
    

    def has_cached_file(
        self,
        path: str,
    ) -> bool:
        """
        Check whether a file exists in session memory.
        """

        memory = self._memory_data()

        return path in memory["files"]


    def cached_files(
        self,
    ) -> dict[str, Any]:
        """
        Return every cached file.
        """

        memory = self._memory_data()

        return memory["files"]

    
    def _append_statistics(
        self,
        message: Message,
    ) -> None:
        index = self._read_json(self._index)

        index["message_count"] += 1

        index["estimated_tokens"] += (
            self._token_counter.count_text(
                message.content
            )
        )

        self._write_json(
            self._index,
            index,
        )

    @staticmethod
    def _sha256(
        content: str,
    ) -> str:
        import hashlib

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()


    def _memory_data(self) -> dict[str, Any]:
        """
        Lazily load session memory once.
        """

        if self._memory_cache is None:
            self._memory_cache = self._read_json(
                self._memory
            )

        return self._memory_cache


    def flush_memory(self) -> None:
        """
        Persist the in-memory cache.
        """

        if self._memory_cache is None:
            return

        self._write_json(
            self._memory,
            self._memory_cache,
        )