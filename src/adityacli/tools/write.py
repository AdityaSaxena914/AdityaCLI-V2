from pathlib import Path

from config import AppConfig
from core.models import Command
from exceptions import FileAlreadyExistsError, InvalidPathError
from tools.base import BaseTool


class WriteTool(BaseTool):
    """Write tool."""

    @property
    def name(self) -> str:
        return "write"

    def execute(self, command: Command) -> str:
        if not command.arguments:
            raise InvalidPathError("At least one file path is required.")

        paths: list[Path] = []

        workspace = self._config.workspace.root.resolve()

        for argument in command.arguments:
            path = (workspace / argument).resolve()

            if not path.is_relative_to(workspace):
                raise InvalidPathError(f"Invalid path: {argument}")

            if path.exists():
                raise FileAlreadyExistsError(f"{argument} already exists.")

            paths.append(path)

        file_list = "\n".join(
            f"=== FILE: {path.relative_to(workspace)} ==="
            for path in paths
        )

        prompt = (
            "Generate the complete contents for the following files.\n\n"
            f"{file_list}\n\n"
            "Return every file in the same format.\n\n"
            "Example:\n"
            "=== FILE: path/to/file ===\n"
            "<content>\n\n"
            f"User Request:\n{command.prompt}"
        )

        return prompt

    def write_files(self, generated: dict[str, str]) -> None:
        workspace = self._config.workspace.root.resolve()

        for relative_path, content in generated.items():
            path = (workspace / relative_path).resolve()

            if not path.is_relative_to(workspace):
                raise InvalidPathError(relative_path)

            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(
                content,
                encoding=self._config.workspace.encoding,
            )