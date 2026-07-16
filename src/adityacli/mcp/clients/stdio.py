from __future__ import annotations

from ..interface import MCPInterface
from ..models import (
    MCPRequest,
    MCPResponse,
    MCPServerInfo,
)

class StdioMCPClient(MCPInterface):
    """MCP client using stdio transport."""

    def __init__(self) -> None:
        self._connected = False

    def info(self) -> MCPServerInfo:
        """Return MCP server metadata."""

        return MCPServerInfo(
            name="stdio",
            description="MCP client using stdio transport.",
        )
    
    def connect(self) -> None:
        """Connect to the MCP server."""

        self._connected = True

    def disconnect(self) -> None:
        """Disconnect from the MCP server."""

        self._connected = False

    def execute(
        self,
        request: MCPRequest,
    ) -> MCPResponse:
        """Execute an MCP request."""

        raise NotImplementedError