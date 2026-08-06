from adityacli.core.models import Message, Role
from adityacli.core.token_counter import CharacterTokenCounter


class ContextManager:
    """Trim conversation history to fit the context window."""

    def __init__(self, context_window: int) -> None:
        self._limit: int = context_window
        self._counter: CharacterTokenCounter = CharacterTokenCounter()

    def trim(
        self,
        messages: list[Message],
    ) -> list[Message]:
        if self._counter.count_messages(messages) <= self._limit:
            return messages

        result: list[Message] = []

        if messages and messages[0].role is Role.SYSTEM:
            result.append(messages[0])

        remaining = messages[1:] if result else messages

        for message in reversed(remaining):
            candidate = [*result, message]

            if self._counter.count_messages(candidate) > self._limit:
                break

            result.insert(1 if result else 0, message)

        return result