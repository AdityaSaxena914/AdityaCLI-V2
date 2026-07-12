from __future__ import annotations

from ..interface import ToolInterface
from ..models import (
    ToolDefinition,
    ToolParameter,
    ToolRequest,
    ToolResult,
)


class WriteFileTool(ToolInterface):
    """Read a file from the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="write_file",
            description="Write content to a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file.",
                    required=True,
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write.",
                    required=True,
                )
            ],
        )
    
    def execute(self, request: ToolRequest) -> ToolResult:
        """Execute the tool."""

        raise NotImplementedError
    
    