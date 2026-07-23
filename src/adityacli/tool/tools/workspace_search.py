from __future__ import annotations
from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter,
    ToolCategory,
    PermissionType
)

class WorkspaceSearchTool(ToolInterface):
    """search a file from the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="workspace_search",
            description="Search files in the current workspace.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query.",
                    required=True,
                ),
            ],
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.READ,
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError()
    
    