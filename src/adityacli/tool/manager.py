from __future__ import annotations

from .interface import ToolInterface
from .registry import ToolRegistry
from .models import (
    ToolRequest,
    ToolResult,
)


class ToolManager:
    """Manage tool execution."""
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(
            self,
            name: str,
            request: ToolRequest,
    ) -> ToolResult:
        """Execute a tool"""

        tool = self._registry.create(name)

        return tool.execute(request)