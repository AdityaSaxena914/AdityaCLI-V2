from __future__ import annotations

from adityacli.config import AppConfig
from adityacli.core.context_manager import ContextManager
from adityacli.core.models import (
    LLMResponse,
    Message,
    ToolResult,
)
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.session import Session
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.exceptions import TruncatedResponseError
from adityacli.llm.client import LLMClient


# The write/edit prompts must instruct the model to emit this exact
# line as the last line of its response. It is passed as a `stop`
# sequence (hard stop at the API level) and also gives ResponseParser
# a positive "the model believes it finished" signal independent of
# hitting the token budget.
END_OF_FILE_SENTINEL = "=== END FILE ==="


class LLMService:
    """
    Responsible for prompt construction and LLM interaction.
    """

    def __init__(
        self,
        client: LLMClient,
        prompt_builder: PromptBuilder,
        config: AppConfig,
    ) -> None:
        self._client: LLMClient = client
        self._prompt_builder: PromptBuilder = prompt_builder
        self._config: AppConfig = config
        self._token_counter: CharacterTokenCounter = CharacterTokenCounter()

        # History budget leaves room for the completion itself; the
        # reserve is shared with _compute_max_tokens below so the two
        # never fight over the same tokens.
        self._context: ContextManager = ContextManager(
            context_window=(
                config.lmstudio.context_window
                - config.lmstudio.completion_reserve_tokens
            )
        )

    def generate(
        self,
        *,
        session: Session,
        tool_result: ToolResult | None,
    ) -> LLMResponse:
        messages: list[Message] = self._prompt_builder.build(
            messages=session.messages,
            tool_result=tool_result,
            read_files=session.read_files,
        )

        messages = self._context.trim(messages)

        max_tokens = self._compute_max_tokens(messages)
        stop = self._stop_sequences(tool_result)

        response = self._client.generate(
            messages,
            max_tokens=max_tokens,
            stop=stop,
        )

        if response.finish_reason == "length":
            raise TruncatedResponseError(
                f"Generation hit the {max_tokens}-token completion "
                "budget before the model finished (context_window="
                f"{self._config.lmstudio.context_window}). Reduce "
                "prompt size, raise context_window, or shorten the "
                "requested output and retry."
            )

        session.add_assistant(response.content)

        return response

    def _compute_max_tokens(self, messages: list[Message]) -> int:
        prompt_tokens_estimate = self._token_counter.count_messages(
            messages
        )

        budget = (
            self._config.lmstudio.context_window
            - prompt_tokens_estimate
            - self._config.lmstudio.completion_reserve_tokens
        )

        # Never send a non-positive or absurdly small budget; a floor
        # keeps this deterministic and loud (a real failure downstream)
        # rather than silently asking for a 1-token completion.
        return max(256, budget)

    def _stop_sequences(
        self,
        tool_result: ToolResult | None,
    ) -> list[str] | None:
        if tool_result is None:
            return None

        if tool_result.metadata.files_written:
            return [END_OF_FILE_SENTINEL]

        return None
