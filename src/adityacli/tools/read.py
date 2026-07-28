from pathlib import Path

from config import AppConfig
from constants import DEFAULT_ENCODING, FILE_HEADER
from core.models import Command
from exceptions import FileTooLargeError, InvalidPathError
from tools.base import BaseTool


class ReadTool(BaseTool):
    """Read tool."""

    @property
    def name(self) -> str:
        return "read"

    def execute(self, command: Command) -> str:
        if len(command.arguments) != 1:
            raise InvalidPathError("Expected exactly one file path.")

        path = self._config.workspace.root / command.arguments[0]
        path = path.resolve()

        workspace = self._config.workspace.root.resolve()

        if not path.is_relative_to(workspace):
            raise InvalidPathError("Path is outside the workspace.")

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise InvalidPathError(f"{path} is not a file.")

        if path.stat().st_size > self._config.workspace.max_file_size:
            raise FileTooLargeError(f"{path} exceeds the maximum file size.")

        content = path.read_text(encoding=DEFAULT_ENCODING)

        return (
            f"{FILE_HEADER.format(path=command.arguments[0])}\n\n"
            f"{content}\n\n"
            f"{command.prompt}"
        )