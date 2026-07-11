from .common import RecoverableError


class ProviderError(RecoverableError):
    """Base class for provider-related errors."""

   
class ProviderOfflineError(ProviderError):
    """Provider is unreachable."""

    ERROR_CODE = "PROVIDER_OFFLINE"

    DEFAULT_RECOVERY_HINT = (
        "Ensure the provider is running and reachable."
    )


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""

    ERROR_CODE = "PROVIDER_TIMEOUT"

    DEFAULT_RECOVERY_HINT = (
        "Retry the request or increase the timeout."
    )


class ProviderAuthenticationError(ProviderError):
    """Authentication with the provider failed."""

    ERROR_CODE = "PROVIDER_AUTHENTICATION"

    DEFAULT_RECOVERY_HINT = (
        "Verify the configured API credentials."
    )


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    ERROR_CODE = "PROVIDER_RATE_LIMIT"

    DEFAULT_RECOVERY_HINT = (
        "Wait before retrying or reduce request frequency."
    )


class ModelNotFoundError(ProviderError):
    """Requested model does not exist."""

    ERROR_CODE = "MODEL_NOT_FOUND"

    DEFAULT_RECOVERY_HINT = (
        "Select an available model."
    )
    

class InvalidProviderResponseError(ProviderError):
    """Provider returned an invalid or unexpected response."""

    ERROR_CODE = "INVALID_PROVIDER_RESPONSE"

    DEFAULT_RECOVERY_HINT = (
        "Retry the request or inspect the provider logs."
    )