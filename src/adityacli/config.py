from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class LMStudioConfig:
    """LM Studio configuration."""

    base_url: str = "http://127.0.0.1:1234/v1"
    api_key: str = "lm-studio"
    model: str = ""

    context_window: int = 15000

    timeout: int = 300


@dataclass(slots=True, frozen=True)
class WorkspaceConfig:
    """Workspace configuration."""

    root: Path
    max_file_size: int = 2 * 1024 * 1024
    encoding: str = "utf-8"
    overwrite_confirmation: bool = True


@dataclass(slots=True, frozen=True)
class SecurityConfig:
    """Security configuration."""

    allow_shell: bool = False
    allow_binary_files: bool = False
    allow_workspace_escape: bool = False


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Application configuration."""

    workspace: WorkspaceConfig
    lmstudio: LMStudioConfig
    security: SecurityConfig