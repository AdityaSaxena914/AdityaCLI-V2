from __future__ import annotations

from adityacli.core.models import Message, Role, ToolResult


class PromptBuilder:
    """Build the temporary message list sent to the LLM."""

    def build(
        self,
        *,
        messages: list[Message],
        tool_result: ToolResult | None,
    ) -> list[Message]:
        prompt = list(messages)

        if tool_result is not None:
            prompt.append(
                Message(
                    role=Role.USER,
                    content=tool_result.prompt,
                )
            )

        return prompt