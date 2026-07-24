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


class ReadFileTool(ToolInterface):
    """Read a file from the active workspace."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="Read the contents of a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path to the file.",
                    required=True,
                )
            ],
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.READ,
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        path = request.arguments.get("path")

        if not isinstance(path, str) or not path.strip():
            raise ToolValidationError(
                "Argument 'path' is required."
            )

        workspace = request.context.workspace_manager

        try:
            file_path = workspace.resolve_existing_file(Path(path))

            return ToolExecutionResult(
                success=True,
                content=file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ),
            )

        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to read '{path}'."
            ) from exc