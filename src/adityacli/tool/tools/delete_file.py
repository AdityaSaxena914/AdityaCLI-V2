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


class DeleteFileTool(ToolInterface):

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delete_file",
            description="Delete a file.",
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.WRITE,
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path.",
                    required=True,
                ),
            ],
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        path = request.arguments.get("path")

        if not isinstance(path, str):
            raise ToolValidationError(
                "Argument 'path' is required."
            )

        try:
            file = request.context.workspace_manager.resolve(
                Path(path)
            )

            file.unlink()

            return ToolExecutionResult(
                success=True,
                content=f"Deleted '{path}'.",
            )

        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to delete '{path}'."
            ) from exc