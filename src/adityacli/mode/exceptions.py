from adityacli.exceptions import RecoverableError

class ModeError(RecoverableError):
    """Base class for all mode-related errors."""

class ModeNotFoundError(ModeError):
    ERROR_CODE = "MODE_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Select a valid execution mode."
    )

class InvalidModeError(ModeError):
    ERROR_CODE = "INVALID_MODE"
    DEFAULT_RECOVERY_HINT = (
        "Verify the selected execution mode."
    )

class ModeTransitionError(ModeError):
    ERROR_CODE = "MODE_TRANSITION"
    DEFAULT_RECOVERY_HINT = (
        "Switch to a compatible execution mode."
    )