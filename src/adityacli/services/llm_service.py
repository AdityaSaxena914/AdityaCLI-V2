from __future__ import annotations
from collections.abc import Iterator
from adityacli.core.models import (
    LLMResponse,
    Message,
    ToolResult,
)
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.session import Session
from adityacli.llm.client import LLMClient
from adityacli.core.token_budget import TokenBudget
from adityacli.core.context_manager import ContextManager



class LLMService:
    """
    Responsible for prompt construction and LLM interaction.
    """

    def __init__(
        self,
        client: LLMClient,
        prompt_builder: PromptBuilder,
        token_budget: TokenBudget,
        context_manager: ContextManager
    ) -> None:
        self._client: LLMClient = client
        self._prompt_builder: PromptBuilder = prompt_builder
        self._token_budget: TokenBudget = token_budget
        self._context_manager: ContextManager = context_manager

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

        messages = self._context_manager.trim(messages)

        self._token_budget.validate(messages)

        response = self._client.generate(messages)

        session.add_assistant(response.content)

        return response

    def stream(
        self,
        *,
        session: Session,
        tool_result: ToolResult | None,
    ) -> Iterator[str]:
        messages = self._prompt_builder.build(
            messages=session.messages,
            tool_result=tool_result,
        )

        messages = self._context_manager.trim(messages)

        self._token_budget.validate(messages)

        for chunk in self._client.stream(messages):
            yield chunk

    @property
    def last_response(self) -> LLMResponse | None:
        return self._client.last_response