from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    MCPRequest,
    MCPResponse,
    MCPServerInfo,
)

class MCPInterface(ABC):
    """Contract implemented by every MCP client."""

    @abstractmethod
    def info(self) -> MCPServerInfo:
        """Return MCP server metadata."""
        ...

    @abstractmethod
    def connect(self) -> None:
        """Connect to the MCP server."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        ...

    @abstractmethod
    def execute(
        self,
        request: MCPRequest,
    ) -> MCPResponse:
        """Execute an MCP request."""
        ...