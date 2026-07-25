from __future__ import annotations

from pathlib import Path

from .exceptions import InvalidWorkspaceError
from .index import WorkspaceIndex
from .models import (
    Workspace,
    WorkspaceInfo,
)
from .resolver import WorkspaceFileResolver
from .validators import WorkspaceValidator
from adityacli.repository import RepositoryManager


class WorkspaceManager:
    """Manage the active workspace."""

    def __init__(self) -> None:
        self._workspace: Workspace | None = None
        self._index: WorkspaceIndex | None = None
        self._resolver: WorkspaceFileResolver | None = None
        self._repository: RepositoryManager | None = None

    @property
    def workspace(self) -> Workspace:
        """Return the active workspace."""

        if self._workspace is None:
            raise InvalidWorkspaceError(
                "Workspace is not loaded."
            )

        return self._workspace

    def load(
        self,
        path: Path,
    ) -> None:
        """Load the workspace."""

        path = WorkspaceValidator.validate_workspace(path)

        self._workspace = Workspace(root=path)

        self._index = WorkspaceIndex(path)
        self._resolver = WorkspaceFileResolver(self._index)

        self._repository = RepositoryManager()
        self._repository.build(path)


    def unload(self) -> None:
        """Unload the active workspace."""

        self._workspace = None
        self._index = None
        self._resolver = None
        self._repository = None
        

    def resolve(
        self,
        path: Path,
    ) -> Path:
        """Resolve a path inside the workspace."""

        return WorkspaceValidator.validate_path(
            self.workspace.root,
            path,
        )

    def resolve_existing_file(
        self,
        path: Path,
    ) -> Path:
        """Resolve an existing file inside the workspace."""

        return WorkspaceValidator.validate_existing_file(
            self.workspace.root,
            path,
        )

    def resolve_file(
        self,
        path: Path,
    ) -> Path:
        """
        Resolve a workspace file.

        Accepts either:
        - full relative path
        - filename only
        """

        try:
            return self.resolve_existing_file(path)
        except Exception:
            pass

        if self._resolver is None:
            raise InvalidWorkspaceError(
                "Workspace index is unavailable."
            )

        resolved = self._resolver.resolve(
            "",
            path,
        )
        if resolved is None:
            return self.resolve_existing_file(path)

        return self.resolve_existing_file(resolved)

    def info(self) -> WorkspaceInfo:
        """Return workspace metadata."""

        return WorkspaceInfo(
            name=self.workspace.root.name,
            root=self.workspace.root,
        )

    def file_candidates(
        self,
        filename: str,
    ) -> list[Path]:
        """Return all workspace files matching a filename."""

        if self._resolver is None:
            raise InvalidWorkspaceError(
                "Workspace index is unavailable."
            )

        return self._resolver.candidates(filename)

    @property
    def repository(self) -> RepositoryManager:
        """Return the repository manager."""

        if self._repository is None:
            raise InvalidWorkspaceError(
                "Repository index is unavailable."
            )

        return self._repository