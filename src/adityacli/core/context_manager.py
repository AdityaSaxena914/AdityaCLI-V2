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

        system = messages[:1] if messages and messages[0].role is Role.SYSTEM else []
        used = self._counter.count_messages(system)
        start = len(system)
        selected: list[Message] = []
        for message in reversed(messages[start:]):
            tokens = self._counter.count_text(message.content)
            if used + tokens > self._limit:
                break
            used += tokens
            selected.append(message)
        selected.reverse()
        while selected and selected[0].role is Role.ASSISTANT:
            selected.pop(0)
        return [*system, *selected]
