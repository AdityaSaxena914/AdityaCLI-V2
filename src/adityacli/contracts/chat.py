from typing import Literal
from pydantic import BaseModel, Field
from .tools import ToolCall


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal[
        "system",
        "user",
        "assistant",
        "tool",
        "developer",
    ]

    content: str

    tool_call_id: str | None = None

    name: str | None = None

    tool_calls: list[ToolCall] = Field(default_factory=list)