from __future__ import annotations

from adityacli.core.models import Message, ToolResult


class PromptBuilder:
    """
    Builds the prompt that will be sent to the LLM.

    Runtime owns orchestration.
    PromptBuilder owns prompt composition.
    """

    def build(
        self,
        *,
        messages: list[Message],
        tool_result: ToolResult | None,
        user_input: str,
    ) -> str:
        sections: list[str] = []

        if tool_result is not None:
            sections.append(tool_result.prompt)

        else:
            sections.append(user_input)

        return "\n\n".join(sections)