from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Role(StrEnum):
    """Chat role."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Tool(StrEnum):
    """Supported tool."""

    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    SEARCH = "search"
    WEB = "web"
    GIT = "git"


@dataclass(slots=True)
class Message:
    """Chat message."""

    role: Role
    content: str


@dataclass(slots=True)
class Command:
    """Parsed command."""

    tool: Tool
    arguments: list[str]
    prompt: str


@dataclass(slots=True)
class SearchResult:
    """Search result."""

    title: str
    url: str
    body: str


@dataclass(slots=True)
class Workspace:
    """Workspace."""

    root: Path


# ---------------------------------------------------------------------------
# Runtime results
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ChatResponse:
    """Normal assistant response."""

    content: str


@dataclass(slots=True)
class OverwriteRequest:
    """
    Pending overwrite confirmation.

    Files maps workspace-relative paths to the generated contents that
    will be written if the user confirms.
    """

    files: dict[str, str]


RuntimeResult = ChatResponse | OverwriteRequest


# ---------------------------------------------------------------------------
# Tool execution models
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class CachedFile:
    """
    A deterministic file that has been collected by a tool.

    Runtime decides whether it should be persisted into session memory.
    """

    path: str
    content: str
    sha256: str


@dataclass(slots=True, frozen=True)
class ToolMetadata:
    """
    Structured metadata returned by deterministic tools.

    Every field is optional.
    Unused fields remain empty.
    """

    files_read: tuple[CachedFile, ...] = ()

    files_written: tuple[str, ...] = ()

    search_results: tuple[str, ...] = ()

    web_urls: tuple[str, ...] = ()

    git_command: str | None = None

    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ToolResult:

    prompt: str
    metadata: ToolMetadata = field(default_factory=ToolMetadata)
    requires_llm: bool = True


@dataclass(slots=True)
class LLMResponse:
    """Language model response."""

    content: str
    model: str

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    elapsed_seconds: float