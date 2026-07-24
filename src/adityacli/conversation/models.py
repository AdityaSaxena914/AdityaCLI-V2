from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ConversationRole = Literal[
    "user",
    "assistant",
]


class ConversationMessage(BaseModel):
    """Single conversation message."""

    role: ConversationRole
    content: str
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
    )


class Conversation(BaseModel):
    """Conversation stored inside a session."""

    messages: list[ConversationMessage] = Field(
        default_factory=list,
    )


@property
def conversation(self) -> Conversation:
    """Return the active conversation."""

    return self._sessions.session.conversation