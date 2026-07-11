from .base import AdityaCLIError


class RecoverableError(AdityaCLIError):
    """Base class for errors that the agent may recover from."""


class FatalError(AdityaCLIError):
    """Base class for unrecoverable application errors."""