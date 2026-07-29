from openai import OpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from adityacli.config import LMStudioConfig
from adityacli.exceptions import ConnectionError, LLMError
from adityacli.core.models import (
    LLMResponse,
    Message,
)
from typing import cast
from time import perf_counter

class LLMClient:
    """LM Studio client."""

    def __init__(self, config: LMStudioConfig) -> None:
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._model = config.model

    def generate(
        self,
        messages: list[Message],
    ) -> LLMResponse:
        """
        Generate a response from the language model.
        """

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
            )

            elapsed = perf_counter() - start
        except OpenAIError as exc:
            raise ConnectionError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        usage = response.usage

        return LLMResponse(
            content=response.choices[0].message.content or "",
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
        )