from __future__ import annotations

from .interface import ToolInterface
from .exceptions import (
    ToolNotFoundError,
    ToolValidationError,
)
from adityacli.contracts.tools import ToolDefinition


class ToolRegistry:
    """Registry of available tool implementations."""


    def __init__(self) -> None:
        self._tools: dict[str, type[ToolInterface]] = {}

    

    def register(
            self,
            name: str,
            tool_class: type[ToolInterface],
    ) -> None:
        """Register a tool implementation."""

        if name in self._tools:
            raise ToolValidationError(
                f"Tool '{name}' is already registered."
            )
        
        self._tools[name] = tool_class


    

    def unregister(self, name: str) -> None:
        """Unregister a tool."""

        if not self.exists(name):
            raise ToolValidationError(
                f"Tool '{name}' is already registered."
            )
        
        del self._tools[name]


    def exists(self, name: str) -> bool:
        """Return whether a tool is registered"""

        return name in self._tools
    

    def create(self, name: str) -> ToolInterface:

        tool_class = self._tools[name]

        return tool_class()
    

    def list_tools(self) -> list[str]:
        """Return all registered tool name"""

        return sorted(self._tools.keys())
    

    def definition(
        self,
        name: str,
    ) -> ToolDefinition:
        """Return a registered tool definition."""

        tool = self.create(name)

        return tool.definition()
    

    def definitions(
        self,
    ) -> list[ToolDefinition]:
        """Return all registered tool definitions."""

        return [
            self.create(name).definition()
            for name in self.list_tools()
    ]