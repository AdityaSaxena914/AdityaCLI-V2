"""
Global constants used throughout AdityaCLI.

This module intentionally contains only immutable values.
No runtime state should ever be stored here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

APP_NAME = "AdityaCLI"
APP_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

PROMPT = "> "

COMMAND_PREFIX = "/"

MULTI_FILE_OPEN = "{"
MULTI_FILE_CLOSE = "}"

# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

WORKSPACE_MARKER = ".git"

MAX_READ_FILE_SIZE = 2 * 1024 * 1024  # 2 MiB

TEXT_FILE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".md",
    ".txt",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".sh",
    ".bat",
    ".ps1",
    ".java",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".sql",
}

# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

FILE_HEADER = "=== FILE: {path} ==="

USER_HEADER = "=== USER REQUEST ==="

# ---------------------------------------------------------------------------
# Tool Names
# ---------------------------------------------------------------------------

TOOL_READ = "read"
TOOL_WRITE = "write"
TOOL_EDIT = "edit"
TOOL_SEARCH = "search"
TOOL_WEB = "web"
TOOL_GIT = "git"

SUPPORTED_TOOLS = frozenset(
    {
        TOOL_READ,
        TOOL_WRITE,
        TOOL_EDIT,
        TOOL_SEARCH,
        TOOL_WEB,
        TOOL_GIT,
    }
)

# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

GIT_EXECUTABLE = "git"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SUBPROCESS_SHELL = False

DEFAULT_ENCODING = "utf-8"

OVERWRITE_CONFIRMATION = "Overwrite? (y/N): "

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path.cwd()