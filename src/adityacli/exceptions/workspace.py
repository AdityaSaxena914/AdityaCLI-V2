from .common import RecoverableError


class WorkspaceError(RecoverableError):
    """Base class for workspace-related errors."""