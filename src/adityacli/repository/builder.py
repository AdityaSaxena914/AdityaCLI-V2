from __future__ import annotations

from pathlib import Path

from adityacli.workspace.index import (
    IGNORED_DIRECTORIES,
)

from .models import RepositoryIndex
from .parser import RepositoryParser


class RepositoryBuilder:
    """Build a repository index from a workspace."""

    def __init__(self) -> None:
        self._parser = RepositoryParser()

    def build(
        self,
        workspace: Path,
    ) -> RepositoryIndex:

        index = RepositoryIndex()

        for path in sorted(workspace.rglob("*.py")):

            if any(
                part in IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            index.files.append(
                self._parser.parse(path)
            )

        return index