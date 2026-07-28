from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


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