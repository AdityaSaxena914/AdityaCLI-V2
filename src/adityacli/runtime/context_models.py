from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ContextSource(str, Enum):
    """Origin of retrieved context."""

    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    SEARCH = "search"
    MCP = "mcp"
    RAG = "rag"
    CONVERSATION = "conversation"


class ContextDocument(BaseModel):
    """Single retrieved context item."""

    source: ContextSource

    title: str

    content: str

    path: Path | None = None

    mime_type: str | None = None

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )


class ContextBundle(BaseModel):
    """Structured context passed to the Prompt Builder."""

    documents: list[ContextDocument] = Field(
        default_factory=list,
    )

    @property
    def empty(self) -> bool:
        return not self.documents