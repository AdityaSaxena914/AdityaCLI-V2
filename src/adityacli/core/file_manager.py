from pathlib import Path

from adityacli.config import AppConfig
from adityacli.exceptions import (
    FileAlreadyExistsError,
    InvalidPathError,
    WriteError,
)


class FileManager:
    """Deterministic filesystem writer."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._workspace = config.workspace.root.resolve()

    def write(
        self,
        relative_path: str,
        content: str,
        overwrite: bool = False,
    ) -> None:
        """
        Write a single text file.
        """

        path = self._resolve(relative_path)

        if path.exists() and not overwrite:
            raise FileAlreadyExistsError(
                f"{relative_path} already exists."
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            path.write_text(
                content,
                encoding=self._config.workspace.encoding,
            )
        except OSError as exc:
            raise WriteError(
                f"Failed to write '{relative_path}'."
            ) from exc

    def write_many(
        self,
        files: dict[str, str],
        overwrite: bool = False,
    ) -> None:
        """
        Write multiple files atomically from the
        caller's perspective.

        Validation is performed for every file before
        any file is written.
        """

        resolved: list[tuple[Path, str, str]] = []

        for relative_path, content in files.items():
            path = self._resolve(relative_path)

            if path.exists() and not overwrite:
                raise FileAlreadyExistsError(
                    f"{relative_path} already exists."
                )

            resolved.append(
                (
                    path,
                    relative_path,
                    content,
                )
            )

        for path, relative_path, content in resolved:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            try:
                path.write_text(
                    content,
                    encoding=self._config.workspace.encoding,
                )
            except OSError as exc:
                raise WriteError(
                    f"Failed to write '{relative_path}'."
                ) from exc

    def _resolve(self, relative_path: str) -> Path:
        """
        Resolve and validate a workspace-relative path.
        """

        path = (self._workspace / relative_path).resolve()

        if not path.is_relative_to(self._workspace):
            raise InvalidPathError(
                f"Path is outside the workspace: {relative_path}"
            )

        return path