from __future__ import annotations
from .registry import ToolRegistry
from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionResult,
    ToolExecutionRequest
)



class ToolManager:
    """Manage tool execution."""


    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry


    def execute(
            self,
            name: str,
            request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        """Execute a tool"""

        tool = self._registry.create(name)

        return tool.execute(request)
    

    def definition(
        self,
        name: str,
    ) -> ToolDefinition:
        """Return a registered tool definition."""

        return self._registry.definition(name)


    def definitions(
        self,
    ) -> list[ToolDefinition]:
        """Return all registered tool definitions."""

        return self._registry.definitions()


    def exists(
        self,
        name: str,
    ) -> bool:
        """Return whether a tool exists."""

        return self._registry.exists(name)