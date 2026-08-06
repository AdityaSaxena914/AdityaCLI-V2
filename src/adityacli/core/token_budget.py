from adityacli.core.models import Message
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.exceptions import ContextWindowExceededError


class TokenBudget:
    """Validate prompt size before sending it to the LLM."""

    def __init__(
        self,
        context_window: int,
    ) -> None:
        self._limit: int = context_window
        self._counter: CharacterTokenCounter = CharacterTokenCounter()

    def validate(
        self,
        messages: list[Message],
    ) -> None:
        tokens = self._counter.count_messages(messages)

        if tokens > self._limit:
            raise ContextWindowExceededError(
                (
                    f"Prompt requires approximately "
                    f"{tokens:,} tokens but only "
                    f"{self._limit:,} are available."
                )
            )