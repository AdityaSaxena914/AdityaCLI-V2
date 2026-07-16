from __future__ import annotations

from pydantic import BaseModel

class MCPServer(BaseModel):
    """Represents an MCP server."""

    name: str

class MCPServerInfo(BaseModel):
    """Metadata about an MCP server."""

    name: str
    description: str

class MCPRequest(BaseModel):
    """MCP request."""

    tool: str
    arguments: dict[str, object]

class MCPResponse(BaseModel):
    """MCP response."""

    success: bool
    output: str | None = None
    error: str | None = None

