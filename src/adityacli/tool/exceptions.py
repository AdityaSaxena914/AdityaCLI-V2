from adityacli.exceptions import RecoverableError


class ToolError(RecoverableError):
    """Base class for all tool-related errors."""

class ToolNotFoundError(ToolError):
    ERROR_CODE = "TOOL_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Verify the tool name."
    )

class ToolExecutionError(ToolError):
    ERROR_CODE = "TOOL_EXECUTION"
    DEFAULT_RECOVERY_HINT = (
        "Retry the operation."
    )

class ToolValidationError(ToolError):
    ERROR_CODE = "TOOL_VALIDATION"
    DEFAULT_RECOVERY_HINT = (
        "Verify the tool arguments."
    )

class ToolPermissionError(ToolError):
    ERROR_CODE = "TOOL_PERMISSION"
    DEFAULT_RECOVERY_HINT = (
        "Request the required permission."
    )

class ToolTimeoutError(ToolError):
    ERROR_CODE = "TOOL_TIMEOUT"
    DEFAULT_RECOVERY_HINT = (
        "Retry the operation or increase the timeout."
    )

class ToolUnavailableError(ToolError):
    ERROR_CODE = "TOOL_UNAVAILABLE"
    DEFAULT_RECOVERY_HINT = (
        "Ensure the required runtime dependency is available."
    )

