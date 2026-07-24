from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from adityacli.conversation import Conversation


class Session(BaseModel):
    """Represents an active application session."""

    id: UUID = Field(default_factory=uuid4)

    conversation: Conversation = Field(
        default_factory=Conversation,
    )


class SessionInfo(BaseModel):
    """Metadata about a session."""

    id: UUID