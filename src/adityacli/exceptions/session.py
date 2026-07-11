from .common import RecoverableError


class SessionError(RecoverableError):
    """Base class for session-related errors."""