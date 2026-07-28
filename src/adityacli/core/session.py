from core.models import Message, Role


class Session:
    """Chat session."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    @property
    def messages(self) -> list[Message]:
        return self._messages

    def add_user(self, content: str) -> None:
        self._messages.append(
            Message(
                role=Role.USER,
                content=content,
            )
        )

    def add_assistant(self, content: str) -> None:
        self._messages.append(
            Message(
                role=Role.ASSISTANT,
                content=content,
            )
        )

    def add_system(self, content: str) -> None:
        self._messages.append(
            Message(
                role=Role.SYSTEM,
                content=content,
            )
        )

    def clear(self) -> None:
        self._messages.clear()