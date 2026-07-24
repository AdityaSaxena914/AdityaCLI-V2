from __future__ import annotations

from .models import (
    IntentResult,
    IntentType,
    PipelineType,
)


class PipelineDispatcher:
    """Select the execution pipeline for a classified request."""

    def dispatch(
        self,
        intent: IntentResult,
    ) -> PipelineType:
        """Return the execution pipeline."""

        match intent.intent:
            case (
                IntentType.FILESYSTEM
                | IntentType.TERMINAL
                | IntentType.GIT
                | IntentType.SEARCH
                | IntentType.WEB
                | IntentType.MCP
            ):
                return PipelineType.DETERMINISTIC

            case IntentType.SEMANTIC:
                return PipelineType.SEMANTIC

            case IntentType.REASONING:
                return PipelineType.REASONING

            case IntentType.AMBIGUOUS:
                raise ValueError(
                    "Unable to determine execution pipeline."
                )

        raise ValueError(
            f"Unsupported intent: {intent.intent.value}"
        )