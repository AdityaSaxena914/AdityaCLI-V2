from __future__ import annotations

from collections.abc import Callable


class ErrorHandler:
    """Convert internal exceptions into user-friendly messages."""

    @staticmethod
    def format(exc: Exception) -> str:
        message = str(exc)

        checks: tuple[
            tuple[Callable[[str], bool], str],
            ...,
        ] = (
            (
                lambda m: "No models loaded" in m,
                (
                    "No model is loaded in LM Studio.\n\n"
                    "Load a model and try again."
                ),
            ),
            (
                lambda m: "exceed_context_size_error" in m,
                (
                    "Conversation exceeded the model context window.\n\n"
                    "Start a new session or clear the current one."
                ),
            ),
            (
                lambda m: "Connection refused" in m,
                (
                    "Unable to connect to LM Studio.\n\n"
                    "Ensure the server is running."
                ),
            ),
            (
                lambda m: "timed out" in m.lower(),
                (
                    "The model took too long to respond."
                ),
            ),
        )

        if isinstance(exc, FileNotFoundError):
            return f"File not found: {exc}"

        for check, friendly in checks:
            if check(message):
                return friendly

        return message