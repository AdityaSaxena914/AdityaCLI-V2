from __future__ import annotations
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import InvalidPathError
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt
from adityacli.core.workspace_guard import WorkspaceGuard


class WriteTool(BaseTool):
    """Generate one or more new files."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._guard = WorkspaceGuard(config)

    def execute(self, command: Command) -> ToolResult:
        if not command.arguments:
            raise InvalidPathError(
                "At least one file path is required."
            )

        paths: list[str] = []

        for relative_path in command.arguments:
            self._guard.new_file(relative_path)
            paths.append(relative_path)

        sections = [
            load_prompt("write"),
        ]

        if command.prompt:
            sections.extend(
                [
                    "",
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