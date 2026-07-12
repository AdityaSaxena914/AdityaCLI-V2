from __future__ import annotations

from .interface import ToolInterface


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
            raise ValueError(
                f"Tool '{name}' is already registered."
            )
        
        self._tools[name] = tool_class
    

    def unregister(self, name: str) -> None:
        """Unregister a tool."""

        if not self.exists(name):
            raise ValueError(
                f"Tool '{name}' is not registered"
            )
        
        del self._tools[name]

    def exists(self, name: str) -> bool:
        """Return whether a tool is registered"""

        return name in self._tools
    
    def create(self, name: str) -> ToolInterface:
        """Create a tool instance."""

        if not self.exists(name):
            raise ValueError(
                f"Tool '{name} is not registered'"
            )
        
        tool_class = self._tools[name]

        return tool_class()
    
    def list_tools(self) -> list[str]:
        """Return all registered tool name"""

        return sorted(self._tools.keys())