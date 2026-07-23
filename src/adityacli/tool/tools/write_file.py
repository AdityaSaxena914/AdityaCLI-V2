from __future__ import annotations

from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolParameter,
    ToolExecutionRequest,
    PermissionType,
    ToolCategory,
    ToolExecutionResult,    
)

class WriteFileTool(ToolInterface):
    """Write a file in the workspace."""

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
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.WRITE,
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError()
    
    