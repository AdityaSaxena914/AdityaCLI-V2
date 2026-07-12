from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

class Workspace(BaseModel):
    """Represents the active workspace."""

    root: Path


class WorkspaceInfo(BaseModel):
    """Metadata about the workspace."""

    name: str
    root: Path