from __future__ import annotations
from ..interface import ToolInterface
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter
)


class GitTool(ToolInterface):
    """Check git branch status."""

    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

        return ToolDefinition(
            name="git_status",
            description="Check git branch status.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Git command to execute.",
                    required=True,
                ),
            ],
        )
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the tool."""

        raise NotImplementedError
    
    