class AdityaCLIError(Exception):
    """Base exception."""


class ParserError(AdityaCLIError):
    """Parser error."""


class InvalidCommandError(ParserError):
    """Unknown command."""


class InvalidSyntaxError(ParserError):
    """Invalid syntax."""


class ValidationError(AdityaCLIError):
    """Validation error."""


class AmbiguousPathError(ValidationError):
    """Raised when a bare filename query matches more than one file."""

    def __init__(self, query: str, candidates: list[str]) -> None:
        self.query: str = query
        self.candidates: list[str] = candidates
        super().__init__(
            f"'{query}' matched {len(candidates)} files: "
            + ", ".join(candidates)
        )


class InvalidPathError(ValidationError):
    """Invalid path."""


class FileAlreadyExistsError(ValidationError):
    """File already exists."""


class FileTooLargeError(ValidationError):
    """File too large."""


class FileOperationError(AdityaCLIError):
    """Filesystem error."""


class WriteError(FileOperationError):
    """Write failed."""


class LLMError(AdityaCLIError):
    """LLM error."""


class LLMConnectionError(LLMError):
    """Connection failed."""


class InvalidResponseError(LLMError):
    """Invalid response."""


class TruncatedResponseError(LLMError):
    """Generation hit the token budget before the model finished."""


class MalformedGenerationError(InvalidResponseError):
    """Generated content failed deterministic structural validation."""


class ToolExecutionError(AdityaCLIError):
    """Raised when a deterministic tool fails during execution."""
