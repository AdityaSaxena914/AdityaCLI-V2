from dataclasses import dataclass, field
from pathlib import Path
from math import isfinite


def _positive(value: int | float, *, integer: bool = False) -> bool:
    return (type(value) is int if integer else type(value) in {int, float}) and isfinite(value) and value > 0


@dataclass(slots=True, frozen=True)
class LMStudioConfig:
    """LM Studio configuration."""

    base_url: str = "http://127.0.0.1:1234/v1"
    api_key: str = "lm-studio"
    model: str = ""

    # Local session-cache sizing default. Inference reads the active
    # context from LM Studio; this value never configures model loading.
    context_window: int = 15000

    timeout: int = 300

    # Tokens deducted from context_window - prompt_tokens when computing
    # the per-request completion budget. Covers estimation error from
    # CharacterTokenCounter (chars/4 approximation) plus formatting
    # overhead, so the model isn't cut off exactly at the wire.
    completion_reserve_tokens: int = 512
    max_response_bytes: int = 2 * 1024 * 1024

    def __post_init__(self) -> None:
        if not _positive(self.timeout) or not _positive(self.context_window, integer=True) or not _positive(self.max_response_bytes, integer=True):
            raise ValueError("Inference timeout, context budget, and output limit must be positive.")
        if type(self.completion_reserve_tokens) is not int or self.completion_reserve_tokens < 0:
            raise ValueError("Completion reserve cannot be negative.")


@dataclass(slots=True, frozen=True)
class WorkspaceConfig:
    """Workspace configuration."""

    root: Path
    max_file_size: int = 2 * 1024 * 1024
    encoding: str = "utf-8"
    overwrite_confirmation: bool = True

    def __post_init__(self) -> None:
        if not _positive(self.max_file_size, integer=True):
            raise ValueError("Maximum file size must be positive.")
        if not self.overwrite_confirmation:
            raise ValueError("Disabling file review is unsupported.")


@dataclass(slots=True, frozen=True)
class SecurityConfig:
    """Security configuration."""

    allow_shell: bool = False
    allow_binary_files: bool = False
    allow_workspace_escape: bool = False

    def __post_init__(self) -> None:
        if self.allow_shell or self.allow_binary_files or self.allow_workspace_escape:
            raise ValueError("Relaxing workspace security is unsupported.")


@dataclass(slots=True, frozen=True)
class ExecutionConfig:
    tool_timeout: float = 30.0
    regex_timeout: float = 2.0
    max_query_chars: int = 8192

    def __post_init__(self) -> None:
        if not _positive(self.tool_timeout) or not _positive(self.regex_timeout) or not _positive(self.max_query_chars, integer=True):
            raise ValueError("Execution limits must be positive.")


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Application configuration."""

    workspace: WorkspaceConfig
    lmstudio: LMStudioConfig
    security: SecurityConfig
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
