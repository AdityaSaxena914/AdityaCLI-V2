from __future__ import annotations

from pathlib import Path
from .exceptions import InvalidWorkspaceError
from .models import (
    Workspace,
    WorkspaceInfo,
)
from .validators import WorkspaceValidator

class WorkspaceManager:
    """Manage the active workspace."""

    def __init__(self) -> None:
        self._workspace: Workspace | None = None

    @property
    def workspace(self) -> Workspace:
        """Return the active workspace."""

        if self._workspace is None:
            raise InvalidWorkspaceError(
                "Workspace is not loaded."
            )

        return self._workspace
    
    def load(self, path: Path) -> None:
        """Load the workspace."""

        path = WorkspaceValidator.validate_workspace(path)
        self._workspace = Workspace(root=path)

    def resolve(self, path: Path) -> Path:
        """Resolve a path inside the workspace."""

        return WorkspaceValidator.validate_path(
            self.workspace.root,
            path,
        )

    def info(self) -> WorkspaceInfo:
        """Return workspace metadata."""

        return WorkspaceInfo(
            name=self.workspace.root.name,
            root=self.workspace.root,
        )
    
    def unload(self) -> None:
        """Unload the active workspace."""

        self._workspace = None

    def resolve_existing_file(
        self,
        path: Path,
    ) -> Path:
        """Resolve an existing file inside the workspace."""

        return WorkspaceValidator.validate_existing_file(
            self.workspace.root,
            path,
        )