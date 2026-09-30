from __future__ import annotations

from adityacli.core.models import Message, Role, ToolResult


class PromptBuilder:
    """Build the temporary message list sent to the LLM."""

    def build(
        self,
        *,
        messages: list[Message],
        tool_result: ToolResult | None,
        read_files: dict[str, str] | None = None,
    ) -> list[Message]:
        prompt = list(messages)

        if read_files:
            sections = "\n".join(
                f"=== FILE: {path} ===\n{content}\n"
                for path, content in read_files.items()
            )

            prompt.append(
                Message(
                    role=Role.USER,
                    content=(
                        "Files read earlier this session, for "
                        "reference:\n\n" + sections
                    ),
                )
            )

        if tool_result is not None:
            prompt.append(
                Message(
                    role=Role.USER,
                    content=tool_result.prompt,
                )
            )

        return prompt
