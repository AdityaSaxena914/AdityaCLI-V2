from __future__ import annotations

from .interface import MCPInterface
from .models import (
    MCPRequest,
    MCPResponse,
)
from .registry import MCPRegistry


class MCPManager:
    """Manage MCP client lifecycle."""

    def __init__(
        self,
        registry: MCPRegistry,
    ) -> None:
        self._registry = registry
        self._client: MCPInterface | None = None

    
    @property
    def client(self) -> MCPInterface | None:
        """Return the active MCP client."""

        return self._client
    

    def connect(
        self,
        name: str,
    ) -> None:
        """Connect to an MCP client."""

        if self._client is not None:
            self._client.disconnect()

        client = self._registry.create(name)

        client.connect()

        self._client = client


    def disconnect(self) -> None:
        """Disconnect the active MCP client."""

        if self._client is None:
            return

        self._client.disconnect()

        self._client = None

    
    def execute(
        self,
        request: MCPRequest,
    ) -> MCPResponse:
        """Execute an MCP request."""

        if self._client is None:
            raise RuntimeError(
                "No active MCP client."
            )

        return self._client.execute(request)