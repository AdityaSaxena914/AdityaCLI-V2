from __future__ import annotations

from pydantic import BaseModel

class ToolParameter(BaseModel):
    """Definition of a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    """Metadata describing a tool."""

    name: str
    description: str
    parameters: list[ToolParameter]


class ToolRequest(BaseModel):
    """Tool execution request."""

    tool: str
    arguments: dict[str, object]


class ToolResult(BaseModel):
    """Standardized tool execution result."""

    success: bool
    output: str | None = None
    error: str | None = None