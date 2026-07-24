from __future__ import annotations

from adityacli.contracts.chat import ChatMessage
from adityacli.conversation.manager import ConversationManager


class MessageBuilder:
    """Build chat messages for the provider."""

    def __init__(
        self,
        conversation: ConversationManager,
    ) -> None:
        self._conversation = conversation

    def build(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> list[ChatMessage]:

        messages: list[ChatMessage] = []

        if system_prompt:
            messages.append(
                ChatMessage(
                    role="system",
                    content=system_prompt,
                )
            )

        for message in self._conversation.messages():
            messages.append(
                ChatMessage(
                    role=message.role,
                    content=message.content,
                )
            )

        messages.append(
            ChatMessage(
                role="user",
                content=user_prompt,
            )
        )

        return messages