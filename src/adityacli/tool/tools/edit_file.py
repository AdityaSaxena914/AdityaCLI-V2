from __future__ import annotations

from ..interface import ToolInterface
from ..models import (
    ToolDefinition,
    ToolParameter,
    ToolRequest,
    ToolResult,
)


class EditFileTool(ToolInterface):
    """Read a file from the workspace."""

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
        )
    
    def execute(self, request: ToolRequest) -> ToolResult:
        """Execute the tool."""

        raise NotImplementedError
    
    