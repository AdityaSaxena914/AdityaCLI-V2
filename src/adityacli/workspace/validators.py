from __future__ import annotations

from pathlib import Path

from .exceptions import (
    InvalidWorkspaceError,
    WorkspaceBoundaryError,
    WorkspaceNotFoundError,
)


class WorkspaceValidator:
    """Validate workspace paths."""

    @staticmethod
    def validate_workspace(path: Path) -> Path:
        """Validate the workspace path."""

        path = path.resolve()

        if not path.exists():
            raise WorkspaceNotFoundError(
                message="Workspace does not exist."
            )

        if not path.is_dir():
            raise InvalidWorkspaceError(
                message="Workspace path is not a director"
            )

        return path
    
    @staticmethod
    def validate_path(
        workspace: Path,
        path: Path,
    ) -> Path:
        """Validate that a path is inside the workspace."""

        workspace = workspace.resolve()
        path = path.resolve()

        if workspace not in path.parents and path != workspace:
            raise WorkspaceBoundaryError(
                message="Path is outside the workspace."
            )

        return path