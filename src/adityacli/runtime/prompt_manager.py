from __future__ import annotations
from .context_models import ContextBundle
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
        context: ContextBundle | None = None,
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

        if context is not None and not context.empty:
            user_prompt = (
                self._serialize_context(context)
                + "\n\n"
                + "## User Request\n"
                + user_prompt
            )

        return PromptContext(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )


    def _serialize_context(
        self,
        context: ContextBundle,
    ) -> str:

        sections: list[str] = [
            "## Retrieved Context",
        ]

        for index, document in enumerate(
            context.documents,
            start=1,
        ):
            sections.append(
                f"\n### Document {index}"
            )

            sections.append(
                f"Source: {document.source.value}"
            )

            sections.append(
                f"Title: {document.title}"
            )

            if document.path is not None:
                sections.append(
                    f"Path: {document.path.as_posix()}"
                )

            if document.mime_type:
                sections.append(
                    f"MIME: {document.mime_type}"
                )

            sections.append("Content:")
            sections.append(document.content)

        return "\n".join(sections)