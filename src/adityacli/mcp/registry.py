from __future__ import annotations

from .interface import MCPInterface

class MCPRegistry:
    """Registry of available MCP client implementations."""

    def __init__(self) -> None:
        self._clients: dict[str, type[MCPInterface]] = {}

    def register(
        self,
        name: str,
        client_class: type[MCPInterface],
    ) -> None:
        """Register an MCP client."""

        if name in self._clients:
            raise ValueError(
                f"MCP client '{name}' is already registered."
            )

        self._clients[name] = client_class

    

    def unregister(self, name: str) -> None:
        """Unregister an MCP client."""

        if not self.exists(name):
            raise ValueError(
                f"MCP client '{name}' is not registered."
            )

        del self._clients[name]

    
    def exists(self, name: str) -> bool:
        """Return whether an MCP client is registered."""

        return name in self._clients
    

    def create(self, name: str) -> MCPInterface:
        """Create an MCP client instance."""

        if not self.exists(name):
            raise ValueError(
                f"MCP client '{name}' is not registered."
            )

        client_class = self._clients[name]

        return client_class()
    

    def list_clients(self) -> list[str]:
        """Return all registered MCP clients."""

        return sorted(self._clients.keys())