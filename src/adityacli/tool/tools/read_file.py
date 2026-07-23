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
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.READ,
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError()
    
    