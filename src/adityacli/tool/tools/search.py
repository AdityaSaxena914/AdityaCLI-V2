from __future__ import annotations
from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter
)

class SearchTool(ToolInterface):
    """search a file from the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="search_file",
            description="search a file from workspace.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query.",
                    required=True,
                ),
            ],
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError
    
    