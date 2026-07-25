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

class AmbiguousFileReferenceError(RuntimeError):
    """Multiple workspace files matched a file reference."""

    ERROR_CODE = "AMBIGUOUS_FILE_REFERENCE"

    def __init__(
        self,
        filename: str,
        matches: list[str],
    ) -> None:
        super().__init__(
            f"Multiple files match '{filename}'."
        )

        self.filename = filename
        self.matches = matches