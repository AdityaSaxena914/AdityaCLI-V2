from __future__ import annotations

from pydantic import BaseModel

class Mode(BaseModel):
    """Represents an execution mode."""

    name: str

class ModeInfo(BaseModel):
    """Metadata about an execution mode."""

    name: str
    description: str

    