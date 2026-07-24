from __future__ import annotations

from pathlib import Path

from adityacli.contracts.tools import (
    PermissionType,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter,
)
from adityacli.tool.exceptions import (
    ToolExecutionError,
    ToolValidationError,
)

from ..interface import ToolInterface


class WriteFileTool(ToolInterface):
    """Write a file inside the active workspace."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_file",
            description="Write content to a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path.",
                    required=True,
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write.",
                    required=True,
                ),
            ],
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.WRITE,
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        path = request.arguments.get("path")
        content = request.arguments.get("content")

        if not isinstance(path, str):
            raise ToolValidationError(
                "Argument 'path' is required."
            )

        if not isinstance(content, str):
            raise ToolValidationError(
                "Argument 'content' is required."
            )

        workspace = request.context.workspace_manager

        try:
            file_path = workspace.resolve(Path(path))

            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path.write_text(
                content,
                encoding="utf-8",
            )

            return ToolExecutionResult(
                success=True,
                content=f"Wrote '{path}'.",
            )

        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to write '{path}'."
            ) from exc