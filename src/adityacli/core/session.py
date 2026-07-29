from __future__ import annotations

from adityacli.core.models import Message, Role
from adityacli.core.session_store import SessionStore


class Session:
    """In-memory chat session backed by SessionStore."""

    def __init__(
        self,
        store: SessionStore | None = None,
    ) -> None:
        self._store = store
        self._messages: list[Message] = []

    @property
    def messages(self) -> list[Message]:
        return self._messages

    def load(self) -> None:
        """
        Restore the persisted session.
        """

        if self._store is None:
            return

        self._messages = self._store.load_messages()

    def add_user(self, content: str) -> None:
        self._append(
            Message(
                role=Role.USER,
                content=content,
            )
        )

    def add_assistant(self, content: str) -> None:
        self._append(
            Message(
                role=Role.ASSISTANT,
                content=content,
            )
        )

    def add_system(self, content: str) -> None:
        self._append(
            Message(
                role=Role.SYSTEM,
                content=content,
            )
        )

    def clear(
        self,
        model: str,
        context_window: int,
    ) -> None:
        self._messages.clear()

        if self._store is not None:
            self._store.clear(
                model=model,
                context_window=context_window,
            )

    def _append(self, message: Message) -> None:
        self._messages.append(message)

        if self._store is not None:
            self._store.append_message(message)