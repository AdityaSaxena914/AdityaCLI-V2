from __future__ import annotations

from ..interface import ToolInterface
from ..models import (
    ToolDefinition,
    ToolParameter,
    ToolRequest,
    ToolResult,
)


class SearchTool(ToolInterface):
    """Read a file from the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="edit_file",
            description="Edit content to a file.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query.",
                    required=True,
                ),
            ],
        )
    
    def execute(self, request: ToolRequest) -> ToolResult:
        """Execute the tool."""

        raise NotImplementedError
    
    