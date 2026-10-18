from __future__ import annotations

from collections.abc import Callable

from adityacli.config import AppConfig
from adityacli.core.context_manager import ContextManager
from adityacli.core.models import (
    LLMResponse,
    Message,
    Role,
    ToolResult,
)
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.session import Session
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.exceptions import LLMError, TruncatedResponseError
from adityacli.core.operations import check_operation
from adityacli.llm.client import LLMClient


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

    def generate(
        self,
        *,
        session: Session,
        tool_result: ToolResult | None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        self._client.health_check()
        context_window = self._client.context_window

        messages: list[Message] = self._prompt_builder.build(
            messages=session.prompt_messages,
            tool_result=tool_result,
            read_files=session.read_files,
        )

        if context_window is not None:
            prompt_limit = context_window - self._config.lmstudio.completion_reserve_tokens - 256
            # A smaller selected model must not silently drop the current
            # request or its file/tool context while trimming old history.
            # Current request is always last. Reference files, when present,
            # form the preceding message and must remain with that request.
            required = messages[-1:]
            if len(messages) > 1 and messages[-2].content.startswith("Reference files (untrusted data):"):
                required = messages[-2:]
            required = [message for message in messages if message.role is Role.SYSTEM and message not in required] + required
            if self._token_counter.count_messages(required) > prompt_limit:
                raise LLMError(
                    f"The current request and file context do not fit this model's "
                    f"{context_window:,}-token context. Clear cached context, shorten "
                    "the request, or increase context in LM Studio."
                )
            messages = ContextManager(context_window=prompt_limit).trim(messages)

        # Unknown context (e.g. a model awaiting JIT loading): let the
        # server apply its own limit rather than guessing a load setting.
        max_tokens = self._compute_max_tokens(messages, context_window) if context_window else None
        generating_file = tool_result is not None and bool(tool_result.metadata.files_written)
        # File drafts stay private until the complete response is validated
        # and shown in the confirmation dialog.
        streaming = {"on_chunk": on_chunk} if on_chunk is not None and not generating_file else {}
        response = self._client.generate(
            messages,
            max_tokens=max_tokens,
            temperature=0.0 if generating_file else None,
            max_response_bytes=self._config.workspace.max_file_size if generating_file else self._config.lmstudio.max_response_bytes,
            **streaming,
        )
        check_operation()
        if generating_file and len(response.content.encode(self._config.workspace.encoding)) > self._config.workspace.max_file_size:
            from adityacli.exceptions import FileTooLargeError
            raise FileTooLargeError("Generated file exceeds the maximum file size.")

        if response.finish_reason == "length":
            limit = f"{max_tokens}-token completion budget" if max_tokens else "server's completion limit"
            raise TruncatedResponseError(
                f"Generation hit the {limit} "
                "before the model finished (context_window="
                f"{context_window or 'managed by LM Studio'}). Reduce "
                "prompt size, increase context in LM Studio, or shorten the "
                "requested output and retry."
            )

        session.add_assistant(
            response.content,
            context=not generating_file,
        )

        return response

    def _compute_max_tokens(self, messages: list[Message], context_window: int) -> int:
        prompt_tokens_estimate = self._token_counter.count_messages(
            messages
        )

        budget = (
            context_window
            - prompt_tokens_estimate
            - self._config.lmstudio.completion_reserve_tokens
        )

        return budget
