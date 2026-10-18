from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias


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
    REMEMBER = "remember"


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
    expected_contents: dict[str, str | None] | None = None


@dataclass(slots=True)
class PendingSelectionRequest:
    """
    Pending disambiguation for a /read query that matched more than
    one file. The CLI's only job is to render `candidates` and send
    back the chosen index — resolution logic itself never lives there.
    """

    query: str
    candidates: tuple[str, ...]
    original_command: Command


RuntimeResult: TypeAlias = (
    ChatResponse
    | OverwriteRequest
    | PendingSelectionRequest
)


# ---------------------------------------------------------------------------
# Tool execution models
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ToolMetadata:
    """
    Structured metadata returned by deterministic tools.

    Every field is optional.
    Unused fields remain empty.
    """

    files_read: tuple[tuple[str, str], ...] = ()

    files_written: tuple[str, ...] = ()

    search_results: tuple[str, ...] = ()

    web_urls: tuple[str, ...] = ()

    git_command: str | None = None

    extra: dict[str, object] = field(default_factory=dict)


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

    finish_reason: str = "stop"


@dataclass(slots=True)
class ResponseStats:
    model: str
    elapsed_seconds: float
    completion_tokens: int
    speed: float
