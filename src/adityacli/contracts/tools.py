from pydantic import BaseModel, Field
from typing import Any


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


class ToolCall(BaseModel):
    """A tool call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    """Result returned by a tool."""

    success: bool = True

    content: str

    metadata: dict[str, Any] = Field(default_factory=dict)

class ToolExecutionRequest(BaseModel):
    """Request passed to a tool implementation."""

    arguments: dict[str, Any] = Field(default_factory=dict)