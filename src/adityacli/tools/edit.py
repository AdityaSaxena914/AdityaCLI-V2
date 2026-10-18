from __future__ import annotations
from typing import override
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import (
    InvalidPathError,
)
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt
from adityacli.core.workspace_guard import WorkspaceGuard


class EditTool(BaseTool):
    """Generate a complete replacement for an existing file."""
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._guard: WorkspaceGuard = WorkspaceGuard(config)

    @override
    def execute(self, command: Command) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidPathError(
                "Expected exactly one file path."
            )

        relative_path = self._guard.relative_path(command.arguments[0])

        content = self._guard.read_text(relative_path, self._config.workspace.encoding)

        prompt = (
            "===== BEGIN UNTRUSTED FILE =====\n"
            + f"=== FILE: {relative_path} ===\n"
            + content
            + "\n===== END UNTRUSTED FILE =====\n=== USER REQUEST ===\n"
            + command.prompt
        )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                files_read=((relative_path, content),),
                files_written=(relative_path,),
                extra={"instructions": load_prompt("edit")},
            ),
        )
