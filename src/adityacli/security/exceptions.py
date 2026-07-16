from adityacli.exceptions import RecoverableError

class SecurityError(RecoverableError):
    """Base class for all security-related errors."""

class PermissionDeniedError(SecurityError):
    ERROR_CODE = "PERMISSION_DENIED"
    DEFAULT_RECOVERY_HINT = (
        "Request the required permission."
    )

class PolicyViolationError(SecurityError):
    ERROR_CODE = "POLICY_VIOLATION"
    DEFAULT_RECOVERY_HINT = (
        "Modify the request to satisfy the active security policy."
    )

class SecurityValidationError(SecurityError):
    ERROR_CODE = "SECURITY_VALIDATION"
    DEFAULT_RECOVERY_HINT = (
        "Verify the security validation rules."
    )

class ConfirmationRequiredError(SecurityError):
    ERROR_CODE = "CONFIRMATION_REQUIRED"
    DEFAULT_RECOVERY_HINT = (
        "Obtain explicit user confirmation."
    )

class RestrictedOperationError(SecurityError):
    ERROR_CODE = "RESTRICTED_OPERATION"
    DEFAULT_RECOVERY_HINT = (
        "This operation is not permitted under the current policy."
    )