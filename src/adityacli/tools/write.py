from __future__ import annotations
from typing import override
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
        self._config: AppConfig = config
        self._guard: WorkspaceGuard = WorkspaceGuard(config)

    @override
    def execute(self, command: Command) -> ToolResult:
        if not command.arguments:
            raise InvalidPathError(
                "At least one file path is required."
            )

        paths: list[str] = []

        for relative_path in command.arguments:
            _=self._guard.new_file(relative_path)
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