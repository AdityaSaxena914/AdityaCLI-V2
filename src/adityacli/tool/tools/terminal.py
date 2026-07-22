from __future__ import annotations
from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter
)

class TerminalTool(ToolInterface):
    """Run a terminal command in the workspace."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="terminal",
            description="ERun terminal command.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Terminal command to execute.",
                    required=True,
                ),
            ],
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError
    
    