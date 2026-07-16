from adityacli.exceptions import RecoverableError

class AgentError(RecoverableError):
    """Base class for all agent-related errors."""

class AgentExecutionError(AgentError):
    ERROR_CODE = "AGENT_EXECUTION"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request."
    )

class AgentNotAvailableError(AgentError):
    ERROR_CODE = "AGENT_NOT_AVAILABLE"
    DEFAULT_RECOVERY_HINT = (
        "Initialize the agent before use."
    )

class AgentConfigurationError(AgentError):
    ERROR_CODE = "AGENT_CONFIGURATION"
    DEFAULT_RECOVERY_HINT = (
        "Verify the agent configuration."
    )

class AgentResponseError(AgentError):
    ERROR_CODE = "AGENT_RESPONSE"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request or inspect provider output."
    )