from __future__ import annotations

from pathlib import Path

from .models import Workspace
from .validators import WorkspaceValidator

class WorkspaceManager:
    """Manage the active workspace."""

    def __init__(self) -> None:
        self._workspace: Workspace | None = None

    @property
    def workspace(self) -> Workspace | None:
        """Return the active workspace."""

        return self._workspace
    
    def load(self, path: Path) -> None:
        """Load the workspace."""

        path = WorkspaceValidator.validate_workspace(path)
        self._workspace = Workspace(root=path)

    def resolve(self, path: Path) -> Path:
        """Resolve a path inside the workspace."""

        if self._workspace is None:
            raise RuntimeError("Workspace is not loaded.")
        
        return WorkspaceValidator.validate_path(
            self._workspace.root,
            path,
        )
    
    def unload(self) -> None:
        """Unload the active workspace."""

        self._workspace = None