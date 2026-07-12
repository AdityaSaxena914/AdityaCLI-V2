from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    ToolDefinition,
    ToolRequest,
    ToolResult,
)

class ToolInterface(ABC):
    """Contract implemented by every tool."""

    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool definition."""

    @abstractmethod
    def execute(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """Execute the tool."""
