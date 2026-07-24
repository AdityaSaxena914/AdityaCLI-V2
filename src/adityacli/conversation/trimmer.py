from __future__ import annotations

from .models import (
    conversation,
    ConversationMessage,
)


class ConversationTrimmer:
    """Trim conversation history to fit a character budget."""

    def trim(
    self,
    messages: list[ConversationMessage],
    character_budget: int,
) -> list[ConversationMessage]:

        if character_budget <= 0:
            return []

        total = 0
        kept: list[ConversationMessage] = []

        for message in reversed(messages):

            size = len(message.content)

            if total + size > character_budget:
                break

            kept.append(message)
            total += size

        kept.reverse()

        return kept