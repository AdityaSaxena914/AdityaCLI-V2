from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """High-level tool categories."""

    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    SEARCH = "search"
    WEB = "web"
    MCP = "mcp"
    CODE_INTELLIGENCE = "code_intelligence"
    HUMAN_INTERACTION = "human_interaction"


class PermissionType(str, Enum):
    """Permissions required to execute a tool."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    GIT = "git"
    MCP = "mcp"


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

    category: ToolCategory

    permission: PermissionType

    parameters: list[ToolParameter]


class ToolCall(BaseModel):
    """A tool call requested by the language model."""

    id: str

    name: str

    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    """Request passed to a tool implementation."""

    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    """Result returned by a tool."""

    success: bool = True

    content: str

    metadata: dict[str, Any] = Field(default_factory=dict)