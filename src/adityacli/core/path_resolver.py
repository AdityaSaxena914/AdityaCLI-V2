from __future__ import annotations

from pathlib import Path

from adityacli.config import AppConfig


_IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    ".sessions",
}


class PathResolver:
    """
    Deterministic filename resolution against the workspace.

    Single source of truth for "given a bare name or fragment, which
    files could this refer to". Used by SearchTool (for display) and
    ReadTool (for resolution before reading), so the two never drift.
    """

    def __init__(self, config: AppConfig) -> None:
        self._workspace: Path = config.workspace.root.resolve()

    @property
    def workspace(self) -> Path:
        return self._workspace

    def find_by_name(self, query: str) -> list[Path]:
        """
        Return absolute paths whose filename or stem matches ``query``
        case-insensitively. Empty list if nothing matches.
        """

        query_lower = query.lower()
        matches: list[Path] = []

        for path in self._workspace.rglob("*"):
            if any(part in _IGNORE_DIRS for part in path.parts):
                continue

            if not path.is_file():
                continue

            stem = path.stem.lower()
            name = path.name.lower()

            if query_lower == stem or query_lower == name:
                matches.append(path)

        return matches
