from adityacli.exceptions import RecoverableError


class RuntimeError(RecoverableError):
    """Base runtime exception."""


class IntentRoutingError(RuntimeError):
    ERROR_CODE = "INTENT_ROUTING"


class ResourceUnavailableError(RuntimeError):
    ERROR_CODE = "RESOURCE_UNAVAILABLE"


class PipelineDispatchError(RuntimeError):
    ERROR_CODE = "PIPELINE_DISPATCH"


class ContextBuilderError(RuntimeError):
    ERROR_CODE = "CONTEXT_BUILDER"


class PromptBuilderError(RuntimeError):
    ERROR_CODE = "PROMPT_BUILDER"