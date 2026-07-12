from adityacli.exceptions import RecoverableError

class ProviderError(RecoverableError):
    """Base class for all provider-related errors."""

class ProviderOfflineError(ProviderError):
    ERROR_CODE = "PROVIDER_OFFLINE"
    DEFAULT_RECOVERY_HINT = (
        "Ensure the provider is running and reachable."
    )

class ProviderTimeoutError(ProviderError):
    ERROR_CODE = "PROVIDER_TIMEOUT"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request or increase the timeout."
    )

class ProviderAuthenticationError(ProviderError):
    ERROR_CODE = "PROVIDER_AUTHENTICATION"
    DEFAULT_RECOVERY_HINT = (
        "Verify the configured credentials."
    )

class ProviderRateLimitError(ProviderError):
    ERROR_CODE = "PROVIDER_RATE_LIMIT"
    DEFAULT_RECOVERY_HINT = (
        "Wait before retrying or reduce request frequency."
    )

class ModelNotFoundError(ProviderError):
    ERROR_CODE = "MODEL_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Select an available model."
    )

class InvalidProviderResponseError(ProviderError):
    ERROR_CODE = "INVALID_PROVIDER_RESPONSE"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request or inspect the provider logs."
    )