from openai import OpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from adityacli.config import LMStudioConfig
from adityacli.exceptions import (
    LLMConnectionError,
    LLMError,
)
from adityacli.core.models import (
    LLMResponse,
    Message,
)
from typing import cast
from time import perf_counter

class LLMClient:
    """LM Studio client."""

    def __init__(self, config: LMStudioConfig) -> None:
        self._client: OpenAI = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

        self._model: str = config.model

    def generate(
        self,
        messages: list[Message],
        *,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """
        Generate a response from the language model.
        """
        self.health_check()

        try:
            payload = cast(
                list[ChatCompletionMessageParam],
                [
                    {
                        "role": message.role.value,
                        "content": message.content,
                    }
                    for message in messages
                ],
            )

            start = perf_counter()

            response = self._client.chat.completions.create(
                model=self._model,
                messages=payload,
                max_tokens=max_tokens,
                stop=stop,
            )

            elapsed = perf_counter() - start
        except OpenAIError as exc:
            raise LLMConnectionError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        usage = response.usage
        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=(
                usage.prompt_tokens if usage else 0
            ),
            completion_tokens=(
                usage.completion_tokens if usage else 0
            ),
            total_tokens=(
                usage.total_tokens if usage else 0
            ),
            elapsed_seconds=elapsed,
            finish_reason=choice.finish_reason or "stop",
        )

    def health_check(self) -> None:
        """
        Verify that LM Studio is reachable and the configured model exists.
        """

        try:
            models = self._client.models.list()
        except OpenAIError as exc:
            raise LLMConnectionError(
                f"Unable to connect to LM Studio: {exc}"
            ) from exc

        available = {
            model.id
            for model in models.data
        }

        if self._model and self._model not in available:
            raise LLMError(
                f"Model '{self._model}' is not loaded in LM Studio."
            )