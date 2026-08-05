from pathlib import Path
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.config import AppConfig
from adityacli.exceptions import (
    FileAlreadyExistsError,
    WriteError,
)


class FileManager:
    """Deterministic filesystem writer."""

    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._guard: WorkspaceGuard = WorkspaceGuard(config)

    def write(
        self,
        relative_path: str,
        content: str,
        overwrite: bool = False,
    ) -> None:
        """
        Write a single text file.
        """

        path = self._guard.new_file(relative_path)

        if path.exists() and not overwrite:
            raise FileAlreadyExistsError(
                f"{relative_path} already exists."
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            _=path.write_text(
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
            path = self._guard.new_file(relative_path)

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
                _=path.write_text(
                    content,
                    encoding=self._config.workspace.encoding,
                )
            except OSError as exc:
                raise WriteError(
                    f"Failed to write '{relative_path}'."
                ) from exc