from __future__ import annotations

from ..interface import ToolInterface
from ..models import (
    ToolDefinition,
    ToolParameter,
    ToolRequest,
    ToolResult,
)


class ReadFileTool(ToolInterface):
    """Read a file from the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="read_file",
            description="Read the content of a file.",
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Path to the file."
                )
            ],
        )
    
    def execute(self, request: ToolRequest) -> ToolResult:
        """Execute the tool."""

        raise NotImplementedError
    
    