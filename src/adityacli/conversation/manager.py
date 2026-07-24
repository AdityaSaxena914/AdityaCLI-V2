from __future__ import annotations

from .models import (
    Conversation,
    ConversationMessage,
)


class ConversationManager:
    """Manage a conversation."""

    def __init__(
        self,
        conversation: Conversation,
    ) -> None:
        self._conversation = conversation

    @property
    def empty(self) -> bool:
        return not self._conversation.messages

    def append_user(
        self,
        content: str,
    ) -> None:
        self._conversation.messages.append(
            ConversationMessage(
                role="user",
                content=content,
            )
        )

    def append_assistant(
        self,
        content: str,
    ) -> None:
        self._conversation.messages.append(
            ConversationMessage(
                role="assistant",
                content=content,
            )
        )

    def messages(self) -> list[ConversationMessage]:
        return list(self._conversation.messages)

    def clear(self) -> None:
        self._conversation.messages.clear()

    def last(self) -> ConversationMessage | None:
        if self.empty:
            return None

        return self._conversation.messages[-1]