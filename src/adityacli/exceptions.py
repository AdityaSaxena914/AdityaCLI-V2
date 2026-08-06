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
    """Ambiguous path."""


class WorkspaceViolationError(ValidationError):
    """Workspace violation."""


class InvalidPathError(ValidationError):
    """Invalid path."""


class FileAlreadyExistsError(ValidationError):
    """File already exists."""


class FileTooLargeError(ValidationError):
    """File too large."""


class BinaryFileError(ValidationError):
    """Binary file."""


class FileOperationError(AdityaCLIError):
    """Filesystem error."""


class ReadError(FileOperationError):
    """Read failed."""


class WriteError(FileOperationError):
    """Write failed."""


class EditError(FileOperationError):
    """Edit failed."""


class LLMError(AdityaCLIError):
    """LLM error."""


class LLMConnectionError(LLMError):
    """Connection failed."""


class InvalidResponseError(LLMError):
    """Invalid response."""


class SecurityError(AdityaCLIError):
    """Security violation."""


class ShellExecutionError(SecurityError):
    """Shell execution blocked."""


class GitError(AdityaCLIError):
    """Git error."""

class ToolExecutionError(AdityaCLIError):
    """Raised when a deterministic tool fails during execution."""

class ContextWindowExceededError(Exception):
    """Prompt exceeds the configured context window."""