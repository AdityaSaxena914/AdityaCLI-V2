from __future__ import annotations
from openai import OpenAI
from typing import cast
from openai.types.chat import ChatCompletionMessageParam
from collections.abc import Iterator
from ..interface import ProviderInterface
from ..models import (
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    ProviderInfo,
)
from adityacli.config import settings



class LMStudioProvider(ProviderInterface):
    """LM Studio provider implementation."""


    def __init__(self) -> None:
        self._base_url = settings.lmstudio.base_url
        self._model = settings.provider.default_model
        self._timeout = settings.lmstudio.timeout

        self._client: OpenAI | None = None
        self._initialized = False


    def initialize(self) -> None:
        """Initialize the LM Studio client."""

        self._client = OpenAI(
            base_url=self._base_url,
            api_key="lm-studio",
            timeout=self._timeout,
        )

        self._initialized = True
    

    def health_check(self) -> bool:
        if self._client is None:
            return False

        try:
            self._client.models.list()
            return True
        except Exception:
            return False
    

    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name="LM Studio",
            endpoint=self._base_url,
        )
    

    def list_models(self) -> list[ModelInfo]:
        if self._client is None:
            raise RuntimeError("Provider not initialized.")

        models = self._client.models.list()

        return [
            ModelInfo(
                id=model.id,
                name=model.id,
            )
            for model in models.data
        ]
    

    def load_model(self, model: str) -> None:
        self._model = model


    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Generate a complete response."""

        if self._client is None:
            raise RuntimeError("Provider not initialized.")

        response = self._client.chat.completions.create(
            model=self._model,
            messages=self._build_messages(request),
            temperature=request.config.temperature,
            max_tokens=request.config.max_tokens,
            stream=False,
        )

        content = response.choices[0].message.content or ""

        return GenerationResponse(
            content=content,
            model=response.model,
            finish_reason=response.choices[0].finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
        )
    

    def generate_stream(
        self,
        request: GenerationRequest,
    ) -> Iterator[str]:
        """Generate a streamed response."""

        if self._client is None:
            raise RuntimeError("Provider not initialized.")

        stream = self._client.chat.completions.create(
            model=self._model,
            messages=self._build_messages(request),
            temperature=request.config.temperature,
            max_tokens=request.config.max_tokens,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content

            if delta:
                yield delta
    

    def _build_messages(
        self,
        request: GenerationRequest,
    ) -> list[ChatCompletionMessageParam]:
        return [
            cast(
                ChatCompletionMessageParam,
                {
                    "role": message.role,
                    "content": message.content,
                },
            )
            for message in request.messages
        ]


    def shutdown(self) -> None:
        """Shutdown the provider."""

        self._client = None
        self._initialized = False