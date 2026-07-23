from __future__ import annotations
from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter,
    PermissionType,
    ToolCategory,
)


class EditFileTool(ToolInterface):
    """edit a file in the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="edit_file",
            description="Edit content to a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file.",
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
                )
            ],
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.WRITE,
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError()
    
    