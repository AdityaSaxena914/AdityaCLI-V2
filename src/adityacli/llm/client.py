from openai import (
    OpenAI,
    OpenAIError,
    Stream,
)
from openai.types.chat import (
    ChatCompletionMessageParam, 
    ChatCompletion,
    ChatCompletionChunk,
)
from collections.abc import Iterator
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
        self._config: LMStudioConfig = config

        self._client: OpenAI = OpenAI(
            api_key="lm-studio",
            base_url=config.host,
        )

        self._model: str = config.model
        self._last_response: LLMResponse | None = None

    def generate(
        self,
        messages: list[Message],
    ) -> LLMResponse:
        """
        Generate a response from the language model.
        """
        self.health_check()

        try:
            payload = self._prepare_payload(messages)

            start = perf_counter()

            response = self._create_request(payload)

            elapsed = perf_counter() - start
        except OpenAIError as exc:
            raise LLMConnectionError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        return self._build_response(
            response=response,
            elapsed=elapsed,
        )

    def _prepare_payload(
        self,
        messages: list[Message],
    ) -> list[ChatCompletionMessageParam]:
        return cast(
            list[ChatCompletionMessageParam],
            [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in messages
            ],
        )

    def _create_request(
        self,
        payload: list[ChatCompletionMessageParam],
    ) -> ChatCompletion:
        return self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            max_tokens=self._config.max_tokens,
            seed=self._config.seed,
        )

    def _create_stream_request(
        self,
        payload: list[ChatCompletionMessageParam],
    ) -> Stream[ChatCompletionChunk]:
        return self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            max_tokens=self._config.max_tokens,
            seed=self._config.seed,
            stream=True,
            stream_options={
                "include_usage": True,
            },
        )


    def stream(
        self,
        messages: list[Message],
    ) -> Iterator[str]:
        self.health_check()

        try:
            payload = self._prepare_payload(messages)

            start = perf_counter()

            response = self._create_stream_request(payload)

            parts: list[str] = []

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            model_name = self._model

            for chunk in response:
                if not model_name and chunk.model:
                    model_name = chunk.model

                if chunk.usage is not None:
                    prompt_tokens = chunk.usage.prompt_tokens
                    completion_tokens = chunk.usage.completion_tokens
                    total_tokens = chunk.usage.total_tokens

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta.content

                if delta:
                    parts.append(delta)
                    yield delta

            elapsed = perf_counter() - start

            self._last_response = LLMResponse(
                content="".join(parts),
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                elapsed_seconds=elapsed,
            )

        except OpenAIError as exc:
            raise LLMConnectionError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    def _build_response(
        self,
        *,
        response: ChatCompletion,
        elapsed: float,
    ) -> LLMResponse:
        
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


    @property
    def last_response(self) -> LLMResponse | None:
        return self._last_response


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