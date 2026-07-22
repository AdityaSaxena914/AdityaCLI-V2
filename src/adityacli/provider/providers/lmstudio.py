from __future__ import annotations
import json
from openai import OpenAI
from typing import cast, Any
from openai.types.chat import ChatCompletionMessageParam
from collections.abc import Iterator
from ..interface import ProviderInterface
from adityacli.config import settings
from adityacli.contracts.generation import GenerationRequest, GenerationResponse
from adityacli.contracts.provider import ProviderInfo, ModelInfo
from adityacli.contracts.tools import ToolCall, ToolDefinition
from adityacli.contracts.chat import ChatMessage



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

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(request),
            "temperature": request.config.temperature,
            "max_tokens": request.config.max_tokens,
            "stream": False,
        }

        if request.tools:
            kwargs["tools"] = self._build_tools(request.tools)

        response = self._client.chat.completions.create(**kwargs)

        message = response.choices[0].message

        print("CONTENT:", message.content)
        print("TOOL CALLS:", message.tool_calls)

        content = message.content or ""

        tool_calls: list[ToolCall] = []

        if message.tool_calls:
            for call in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=call.id,
                        name=call.function.name,
                        arguments = json.loads(call.function.arguments),
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
            raise RuntimeError("Provider not initialized.")

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(request),
            "temperature": request.config.temperature,
            "max_tokens": request.config.max_tokens,
            "stream": True,
        }

        if request.tools:
            kwargs["tools"] = self._build_tools(request.tools)

        stream = self._client.chat.completions.create(**kwargs)

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
        self._initialized = False