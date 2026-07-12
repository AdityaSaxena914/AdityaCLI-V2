from adityacli.exceptions import RecoverableError

class SessionError(RecoverableError):
    """Base class for all session-related errors."""

class SessionNotFoundError(SessionError):
    ERROR_CODE = "SESSION_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Create or load a valid session."
    )

class SessionAlreadyExistsError(SessionError):
    ERROR_CODE = "SESSION_ALREADY_EXISTS"
    DEFAULT_RECOVERY_HINT = (
        "Use the existing session or create a new one."
    )

class SessionNotActiveError(SessionError):
    ERROR_CODE = "SESSION_NOT_ACTIVE"
    DEFAULT_RECOVERY_HINT = (
        "Start a session before performing this operation."
    )

class InvalidSessionError(SessionError):
    ERROR_CODE = "INVALID_SESSION"
    DEFAULT_RECOVERY_HINT = (
        "Verify the session state."
    )