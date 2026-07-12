from adityacli.exceptions import RecoverableError

class WorkspaceError(RecoverableError):
    """Base class for all workspace-related errors."""

class WorkspaceNotFoundError(WorkspaceError):
    ERROR_CODE = "WORKSPACE_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Verify the workspace path exists."
    )

class WorkspaceAccessDeniedError(WorkspaceError):
    ERROR_CODE = "WORKSPACE_ACCESS_DENIED"
    DEFAULT_RECOVERY_HINT = (
        "Verify file and directory permissions."
    )

class WorkspaceBoundaryError(WorkspaceError):
    ERROR_CODE = "WORKSPACE_BOUNDARY"
    DEFAULT_RECOVERY_HINT = (
        "Access files only inside the workspace."
    )

class InvalidWorkspaceError(WorkspaceError):
    ERROR_CODE = "INVALID_WORKSPACE"
    DEFAULT_RECOVERY_HINT = (
        "Select a valid project directory."
    )