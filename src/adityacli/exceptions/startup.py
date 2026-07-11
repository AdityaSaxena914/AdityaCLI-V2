from .common import FatalError


class StartupError(FatalError):
    """Application failed during startup."""


class InternalError(FatalError):
    """Unexpected internal application failure."""