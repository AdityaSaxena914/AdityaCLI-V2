from __future__ import annotations

from adityacli.core.models import (
    LLMResponse,
    Message,
    ToolResult,
)
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.session import Session
from adityacli.llm.client import LLMClient


class LLMService:
    """
    Responsible for prompt construction and LLM interaction.
    """

    def __init__(
        self,
        client: LLMClient,
        prompt_builder: PromptBuilder,
    ) -> None:
        self._client: LLMClient = client
        self._prompt_builder: PromptBuilder = prompt_builder

    def generate(
        self,
        *,
        session: Session,
        tool_result: ToolResult | None,
    ) -> LLMResponse:
        messages: list[Message] = self._prompt_builder.build(
            messages=session.messages,
            tool_result=tool_result,
        )

        response = self._client.generate(messages)

        session.add_assistant(response.content)

        return response