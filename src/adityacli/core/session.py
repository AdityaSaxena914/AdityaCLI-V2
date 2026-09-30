from __future__ import annotations

from adityacli.core.models import Message, Role
from adityacli.core.session_store import SessionStore
from adityacli.core.token_counter import CharacterTokenCounter


class Session:
    """In-memory chat session backed by SessionStore."""

    def __init__(
        self,
        store: SessionStore,
        max_read_tokens: int = 4000,
    ) -> None:
        self._store: SessionStore = store
        self._messages: list[Message] = []
        self._read_files: dict[str, str] = {}
        self._max_read_tokens: int = max_read_tokens
        self._counter: CharacterTokenCounter = CharacterTokenCounter()

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def read_files(self) -> dict[str, str]:
        """
        Files read this session (path -> content), most-recently-read
        last. Injected fresh into every LLM call so a follow-up
        question can refer to them, without being duplicated into the
        persisted conversation transcript itself.
        """

        return self._read_files

    def load(self) -> None:
        """
        Restore the persisted session.
        """

        self._messages = self._store.load_messages()
        self._read_files = self._store.read_memory()

    def add_user(self, content: str) -> None:
        self._append(Message(role=Role.USER, content=content))

    def add_assistant(self, content: str) -> None:
        self._append(Message(role=Role.ASSISTANT, content=content))

    def add_system(self, content: str) -> None:
        if self._messages:
            if self._messages[0].role is Role.SYSTEM:
                return

            self._messages.insert(
                0,
                Message(role=Role.SYSTEM, content=content),
            )
            return

        self._append(Message(role=Role.SYSTEM, content=content))

    def remember_file(self, path: str, content: str) -> None:
        """
        Record a file that was read so later plain-chat turns can
        still refer to it. Bounded by max_read_tokens: oldest-read
        file is dropped first once the budget is exceeded, so this
        never becomes an unbounded, ever-growing context leak.
        """

        self._read_files.pop(path, None)
        self._read_files[path] = content

        while (
            self._total_read_tokens() > self._max_read_tokens
            and len(self._read_files) > 1
        ):
            oldest = next(iter(self._read_files))
            del self._read_files[oldest]

        self._store.write_read_memory(self._read_files)

    def _total_read_tokens(self) -> int:
        return sum(
            self._counter.count_text(content)
            for content in self._read_files.values()
        )

    def clear(self, model: str, context_window: int) -> None:
        self._messages.clear()
        self._read_files.clear()

        self._store.clear(model=model, context_window=context_window)

    def _append(self, message: Message) -> None:
        self._messages.append(message)
        self._store.append_message(message)
