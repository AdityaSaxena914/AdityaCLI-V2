from pathlib import Path

from config import AppConfig
from constants import DEFAULT_ENCODING, FILE_HEADER
from core.models import Command
from exceptions import FileTooLargeError, InvalidPathError
from tools.base import BaseTool


class EditTool(BaseTool):
    """Edit tool."""

    @property
    def name(self) -> str:
        return "edit"

    def execute(self, command: Command) -> str:
        if len(command.arguments) != 1:
            raise InvalidPathError("Expected exactly one file path.")

        workspace = self._config.workspace.root.resolve()
        relative_path = command.arguments[0]

        path = (workspace / relative_path).resolve()

        if not path.is_relative_to(workspace):
            raise InvalidPathError("Path is outside the workspace.")

        if not path.exists():
            raise FileNotFoundError(relative_path)

        if not path.is_file():
            raise InvalidPathError(f"{relative_path} is not a file.")

        if path.stat().st_size > self._config.workspace.max_file_size:
            raise FileTooLargeError(f"{relative_path} exceeds the maximum file size.")

        content = path.read_text(encoding=DEFAULT_ENCODING)

        return (
            "Modify the following file according to the user's request.\n\n"
            "Return ONLY the complete updated file contents.\n\n"
            f"{FILE_HEADER.format(path=relative_path)}\n\n"
            f"{content}\n\n"
            f"User Request:\n{command.prompt}"
        )

    def write_file(self, relative_path: str, content: str) -> None:
        workspace = self._config.workspace.root.resolve()

        path = (workspace / relative_path).resolve()

        if not path.is_relative_to(workspace):
            raise InvalidPathError(relative_path)

        path.write_text(
            content,
            encoding=self._config.workspace.encoding,
        )