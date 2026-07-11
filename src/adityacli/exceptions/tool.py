from .common import RecoverableError


class ToolError(RecoverableError):
    """Base class for tool-related errors."""