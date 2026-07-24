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


class EditFileTool(ToolInterface):
    """Replace text inside an existing file."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="edit_file",
            description="Replace text inside a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path.",
                    required=True,
                ),
                ToolParameter(
                    name="old_text",
                    type="string",
                    description="Text to replace.",
                    required=True,
                ),
                ToolParameter(
                    name="new_text",
                    type="string",
                    description="Replacement text.",
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
        old_text = request.arguments.get("old_text")
        new_text = request.arguments.get("new_text")

        if not isinstance(path, str):
            raise ToolValidationError(
                "Argument 'path' is required."
            )

        if not isinstance(old_text, str):
            raise ToolValidationError(
                "Argument 'old_text' is required."
            )

        if not isinstance(new_text, str):
            raise ToolValidationError(
                "Argument 'new_text' is required."
            )

        workspace = request.context.workspace_manager

        try:
            file_path = workspace.resolve(Path(path))

            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if old_text not in content:
                raise ToolExecutionError(
                    "Text not found."
                )

            replacements = content.count(old_text)

            updated = content.replace(
                old_text,
                new_text,
            )

            file_path.write_text(
                updated,
                encoding="utf-8",
            )

            return ToolExecutionResult(
                success=True,
                content=f"Updated '{path}'.",
                metadata={
                    "replacements": replacements,
                },
            )

        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to edit '{path}'."
            ) from exc