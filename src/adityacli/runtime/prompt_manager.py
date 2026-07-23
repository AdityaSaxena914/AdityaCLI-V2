from __future__ import annotations

from .models import (
    PipelineType,
    PromptContext,
)


class PromptManager:
    """Build prompts for each execution pipeline."""

    def build(
        self,
        pipeline: PipelineType,
        user_prompt: str,
        context: str | None = None,
    ) -> PromptContext:
        """Build the final prompt."""

        if pipeline == PipelineType.DETERMINISTIC:
            system_prompt = (
                "Execute the requested task accurately."
            )

        elif pipeline == PipelineType.SEMANTIC:
            system_prompt = (
                "Answer only using the supplied context."
            )

        elif pipeline == PipelineType.REASONING:
            system_prompt = (
                "Reason carefully before producing the final answer."
            )

        else:
            system_prompt = (
                "Request clarification from the user."
            )

        if context:
            user_prompt = (
                f"{context}\n\n"
                f"{user_prompt}"
            )

        return PromptContext(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )