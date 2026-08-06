from __future__ import annotations

from pathlib import Path

from adityacli.config import AppConfig
from adityacli.exceptions import (
    FileTooLargeError,
    InvalidPathError,
)


class WorkspaceGuard:
    """Centralized workspace path validation."""

    def __init__(self, config: AppConfig) -> None:
        self._workspace: Path = config.workspace.root.resolve()
        self._max_file_size: int = config.workspace.max_file_size

    def resolve(self, relative_path: str) -> Path:
        path = (self._workspace / relative_path).resolve()

        if not path.is_relative_to(self._workspace):
            raise InvalidPathError(
                f"Path is outside the workspace: {relative_path}"
            )

        return path

    def existing_file(self, relative_path: str) -> Path:
        path = self.resolve(relative_path)

        if not path.exists():
            raise FileNotFoundError(relative_path)

        if not path.is_file():
            raise InvalidPathError(
                f"{relative_path} is not a file."
            )

        if path.stat().st_size > self._max_file_size:
            raise FileTooLargeError(
                f"{relative_path} exceeds the maximum file size."
            )

        return path

    def new_file(self, relative_path: str) -> Path:
        return self.resolve(relative_path)

    def find_files(
        self,
        filename: str,
    ) -> list[Path]:
        ignored = {
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            "build",
            "dist",
        }

        matches: list[Path] = []

        for path in self._workspace.rglob(filename):
            if any(part in ignored for part in path.parts):
                continue

            if path.is_file():
                matches.append(path)

        return matches