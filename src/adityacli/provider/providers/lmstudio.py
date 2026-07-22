from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any, cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from adityacli.config import settings
from adityacli.contracts.chat import ChatMessage
from adityacli.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)
from adityacli.contracts.provider import (
    ModelInfo,
    ProviderInfo,
)
from adityacli.contracts.tools import (
    ToolCall,
    ToolDefinition,
)

from ..exceptions import (
    InvalidProviderResponseError,
    ModelNotFoundError,
    ProviderOfflineError,
)
from ..interface import ProviderInterface



class LMStudioProvider(ProviderInterface):
    """LM Studio provider implementation."""


    def __init__(self) -> None:
        self._base_url = settings.lmstudio.base_url
        self._timeout = settings.lmstudio.timeout

        self._client: OpenAI | None = None

        self._model: str | None = None
        self._model_info: ModelInfo | None = None

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
        """Return whether the provider is reachable."""

        if self._client is None:
            return False

        try:
            self._client.models.list()
            return True
        except Exception:
            return False
    

    def provider_info(self) -> ProviderInfo:
        """Return provider information."""

        return ProviderInfo(
            name="LM Studio",
            endpoint=self._base_url,
            online=self.health_check(),
        )
    

    def list_models(self) -> list[ModelInfo]:
        """Return all available models."""

        if self._client is None:
            raise ProviderOfflineError("Provider Offline")

        try:
            models = self._client.models.list()

            return [
                ModelInfo(
                    id=model.id,
                    name=model.id,
                    context_window=0,
                    quantization=None,
                    estimated_ram_mb=None,
                    supports_streaming=True,
                    supports_tools=True,
                    supports_grammar=False,
                )
                for model in models.data
            ]

        except Exception as exc:
            raise InvalidProviderResponseError("Invalid Response") from exc
    

    def model_info(self) -> ModelInfo:
        """Return information about the active model."""

        if self._model_info is None:
            raise ModelNotFoundError("Model not found")

        return self._model_info

    
    def load_model(self, model: str) -> None:
        """Load a model."""

        self._model = model

        self._model_info = ModelInfo(
            id=model,
            name=model,
            context_window=0,
            quantization=None,
            estimated_ram_mb=None,
            supports_streaming=True,
            supports_tools=True,
            supports_grammar=False,
        )


    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Generate a complete response."""

        if self._client is None:
            raise ProviderOfflineError("Provider is Offline.")

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(request),
            "temperature": request.config.temperature,
            "max_tokens": request.config.max_tokens,
            "stream": False,
        }

        if request.tools:
            kwargs["tools"] = self._build_tools(request.tools)

        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise InvalidProviderResponseError("invalid Provider Response.") from exc

        message = response.choices[0].message


        content = message.content or ""

        tool_calls: list[ToolCall] = []

        if message.tool_calls:
            for call in message.tool_calls:
                try:
                    arguments = json.loads(call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=call.id,
                        name=call.function.name,
                        arguments=arguments,
                    )
                )

        return GenerationResponse(
            message=ChatMessage(
                role="assistant",
                content=content,
                tool_calls=tool_calls,
            ),
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
            raise ProviderOfflineError("Provider is Offline.")

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(request),
            "temperature": request.config.temperature,
            "max_tokens": request.config.max_tokens,
            "stream": True,
        }

        if request.tools:
            kwargs["tools"] = self._build_tools(request.tools)

        try:
            stream = self._client.chat.completions.create(**kwargs)
        except Exception as exc:
                    raise InvalidProviderResponseError("invalid Provider Response.") from exc
        
        for chunk in stream:
            delta = chunk.choices[0].delta.content

            if delta:
                yield delta
    

    def _build_messages(
        self,
        request: GenerationRequest,
    ) -> list[ChatCompletionMessageParam]:
        messages: list[ChatCompletionMessageParam] = []

        for message in request.messages:
            msg = {
                "role": message.role,
                "content": message.content,
            }

            if message.name:
                msg["name"] = message.name

            if message.tool_call_id:
                msg["tool_call_id"] = message.tool_call_id

            messages.append(cast(ChatCompletionMessageParam, msg))

        return messages
    

    def _build_tools(
        self,
        tools: list[ToolDefinition],
    ) -> list[dict[str, Any]]:
        """Convert ToolDefinition objects into OpenAI tool schema."""

        schemas: list[dict[str, Any]] = []

        for tool in tools:
            properties: dict[str, Any] = {}
            required: list[str] = []

            for parameter in tool.parameters:
                properties[parameter.name] = {
                    "type": parameter.type,
                    "description": parameter.description,
                }

                if parameter.required:
                    required.append(parameter.name)

            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    },
                }
            )

        return schemas


    def shutdown(self) -> None:
        """Shutdown the provider."""

        self._client = None

        self._model = None
        self._model_info = None

        self._initialized = False