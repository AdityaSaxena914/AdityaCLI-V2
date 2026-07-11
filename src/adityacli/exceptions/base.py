from __future__ import annotations
from typing import Any


class AdityaCLIError(Exception):
    """Base exception for all AdityaCLI errors."""

    ERROR_CODE = "UNKNOWN_ERROR"
    DEFAULT_RECOVERY_HINT: str | None = None

    def __init__(
            self,
            message: str,
            *,
            error_code: str | None = None,
            recovery_hint: str | None = None,
            cause: Exception | None = None,
            metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.error_code = (
            error_code 
            or self.ERROR_CODE
        )
        self.recovery_hint = (
            recovery_hint 
            or self.DEFAULT_RECOVERY_HINT
        )
        self.cause = cause
        self.metadata = metadata or {}