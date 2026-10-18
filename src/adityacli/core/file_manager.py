import os
import tempfile

from adityacli.config import AppConfig
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import FileAlreadyExistsError, FileTooLargeError, WriteError
from adityacli.exceptions import ValidationError
from adityacli.core.locking import file_lock
from adityacli.core.operations import check_operation


class FileManager:
    """Validate all targets first; replace each file atomically."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._guard = WorkspaceGuard(config)

    def write(self, relative_path: str, content: str, overwrite: bool = False) -> None:
        self.write_many({relative_path: content}, overwrite=overwrite)

    def validate_content(self, content: str, path: str) -> None:
        if len(content.encode(self._config.workspace.encoding)) > self._config.workspace.max_file_size:
            raise FileTooLargeError(f"{path} exceeds the maximum file size.")

    def write_many(self, files: dict[str, str], overwrite: bool = False,
                   expected_contents: dict[str, str | None] | None = None) -> None:
        # All AdityaCLI writers use the same cross-process lock, including the
        # version check. Noncooperating OS writers require native protection.
        with file_lock(self._guard.resolve(".sessions/files.lock")):
            self._write_many_locked(files, overwrite, expected_contents)

    def _write_many_locked(self, files: dict[str, str], overwrite: bool,
                           expected_contents: dict[str, str | None] | None) -> None:
        for relative_path, content in files.items():
            check_operation()
            path = self._guard.new_file(relative_path)
            self.validate_content(content, relative_path)
            if path.exists() and not overwrite:
                raise FileAlreadyExistsError(f"{relative_path} already exists.")
        for relative_path, content in files.items():
            temporary: str | None = None
            try:
                path = self._guard.new_file(relative_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path = self._guard.new_file(relative_path)
                fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
                with os.fdopen(fd, "w", encoding=self._config.workspace.encoding, newline="") as file:
                    file.write(content)
                    file.flush()
                    os.fsync(file.fileno())
                path = self._guard.new_file(relative_path)
                check_operation()
                if path.exists() and not overwrite:
                    raise FileAlreadyExistsError(f"{relative_path} already exists.")
                if expected_contents is not None and relative_path in expected_contents:
                    current = self.read(relative_path) if path.exists() else None
                    if current != expected_contents[relative_path]:
                        raise ValidationError(f"File changed since generation started: {relative_path}. Generate and review the changes again.")
                os.replace(temporary, path)
            except OSError as exc:
                raise WriteError(f"Failed to write '{relative_path}'.") from exc
            finally:
                if temporary is not None and os.path.exists(temporary):
                    os.remove(temporary)

    def exists(self, relative_path: str) -> bool:
        return self._guard.new_file(relative_path).exists()

    def read(self, relative_path: str) -> str:
        return self._guard.read_text(relative_path, self._config.workspace.encoding)
