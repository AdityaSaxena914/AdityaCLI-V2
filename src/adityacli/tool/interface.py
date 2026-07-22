from __future__ import annotations

from abc import ABC, abstractmethod
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult
)

class ToolInterface(ABC):
    """Contract implemented by every tool."""

    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

    @abstractmethod
    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        """Execute the tool."""
