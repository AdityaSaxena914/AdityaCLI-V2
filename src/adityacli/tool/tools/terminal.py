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

class TerminalTool(ToolInterface):
    """Run a terminal command in the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="terminal",
            description="Run a terminal command.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Terminal command to execute.",
                    required=True,
                ),
            ],
            category=ToolCategory.TERMINAL,
            permission=PermissionType.EXECUTE,
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError()
    
    