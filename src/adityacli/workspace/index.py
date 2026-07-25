from __future__ import annotations

from collections import defaultdict
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "node_modules",
}


class WorkspaceIndex:
    """Indexes files inside the active workspace."""

    def __init__(
        self,
        root: Path,
    ) -> None:
        self._root = root
        self._files: dict[str, list[Path]] = defaultdict(list)

        self.rebuild()

    def rebuild(self) -> None:
        """Rebuild the workspace index."""

        self._files.clear()

        for path in self._root.rglob("*"):

            if not path.is_file():
                continue

            if any(
                part in IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            relative = path.relative_to(self._root)

            self._files[path.name.lower()].append(relative)

        for paths in self._files.values():
            paths.sort(
                key=lambda p: (
                    len(p.parts),
                    len(p.as_posix()),
                    p.as_posix(),
                )
            )

    def lookup(
        self,
        filename: str,
    ) -> list[Path]:
        """Return every matching file."""

        return list(
            self._files.get(
                filename.lower(),
                [],
            )
        )