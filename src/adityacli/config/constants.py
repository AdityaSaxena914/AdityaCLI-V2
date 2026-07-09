"""Application-wide constants.

Constants in this file are part of AdityaCLI's design.
They are NOT configurable through environment variables.
"""

APP_NAME = "AdityaCLI"
APP_VERSION = "2.0.0"

SESSION_RETENTION_DAYS = 30

SUPPORTED_PROVIDERS = (
    "lmstudio",
    "ollama",
    "openai",
    "anthropic",
    "gemini",
)