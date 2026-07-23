from __future__ import annotations

from .models import (
    IntentResult,
    PipelineType,
)


class PipelineDispatcher:
    """Dispatch requests to the appropriate execution pipeline."""

    def dispatch(
        self,
        intent: IntentResult,
    ) -> PipelineType:
        """Return the selected execution pipeline."""

        match intent.pipeline:
            case PipelineType.DETERMINISTIC:
                return PipelineType.DETERMINISTIC

            case PipelineType.SEMANTIC:
                return PipelineType.SEMANTIC

            case PipelineType.REASONING:
                return PipelineType.REASONING

            case PipelineType.AMBIGUOUS:
                return PipelineType.AMBIGUOUS

        raise ValueError(
            f"Unsupported pipeline: {intent.pipeline}"
        )