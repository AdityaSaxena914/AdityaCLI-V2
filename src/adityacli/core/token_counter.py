from __future__ import annotations

from abc import ABC, abstractmethod
from typing import override
from adityacli.core.models import Message

class BaseTokenCounter(ABC):
    """Estimate token usage."""

    @abstractmethod
    def count_text(
        self,
        text: str,
    ) -> int:
        raise NotImplementedError


class CharacterTokenCounter(BaseTokenCounter):
    """
    Deterministic approximation.

    ~4 characters ≈ 1 token.
    """

    CHARS_PER_TOKEN: int = 4

    @override
    def count_text(
        self,
        text: str,
    ) -> int:
        if not text:
            return 0

        return max(
            1,
            (len(text) + self.CHARS_PER_TOKEN - 1)
            // self.CHARS_PER_TOKEN,
        )

    def count_messages(
        self,
        messages: list[Message],
    ) -> int:
        total = 0

        for message in messages:
            total += self.count_text(message.content)

        return total