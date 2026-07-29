from __future__ import annotations
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import (
    FileAlreadyExistsError,
    InvalidPathError,
)
from adityacli.tools.base import BaseTool


class WriteTool(BaseTool):
    """Generate one or more new files."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._workspace = config.workspace.root.resolve()

    def execute(self, command: Command) -> ToolResult:
        if not command.arguments:
            raise InvalidPathError(
                "At least one file path is required."
            )

        paths: list[str] = []

        for relative_path in command.arguments:
            path = (self._workspace / relative_path).resolve()

            if not path.is_relative_to(self._workspace):
                raise InvalidPathError(
                    f"Invalid path: {relative_path}"
                )

            if path.exists():
                raise FileAlreadyExistsError(
                    f"{relative_path} already exists."
                )

            paths.append(relative_path)

        sections = [
            "Generate the complete contents for every requested file.",
            "",
            "Return ONLY the following format:",
            "",
        ]

        for path in paths:
            sections.append(f"=== FILE: {path} ===")
            sections.append("<complete file contents>")
            sections.append("")

        if command.prompt:
            sections.extend(
                [
                    "User Request:",
                    command.prompt,
                ]
            )

        return ToolResult(
            prompt="\n".join(sections),
            metadata=ToolMetadata(
                files_written=tuple(paths),
            ),
        )