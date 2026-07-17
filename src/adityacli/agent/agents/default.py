from __future__ import annotations

from adityacli.provider import (
    ChatMessage,
    GenerationConfig,
    GenerationRequest,
    ProviderManager,
)
from collections.abc import Iterator
from ..interface import AgentInterface
from ..models import (
    AgentInfo,
    AgentRequest,
    AgentResponse,
)


class DefaultAgent(AgentInterface):
    """Default agent implementation."""

    def __init__(
        self,
        provider_manager: ProviderManager,
    ) -> None:
        self._provider_manager = provider_manager

    def info(self) -> AgentInfo:
        return AgentInfo(
            name="default",
            description="Default AdityaCLI agent.",
        )

    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        provider = self._provider_manager.active_provider

        if provider is None:
            raise RuntimeError("No active provider.")

        response = provider.generate(
            GenerationRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content=request.prompt,
                    )
                ],
                config=GenerationConfig(),
            )
        )

        return AgentResponse(
            response=response.content,
        )
    
    def execute_stream(
        self,
        request: AgentRequest,
    ) -> Iterator[str]:
        """Execute the agent with streaming."""

        provider = self._provider_manager.active_provider

        if provider is None:
            raise RuntimeError("No active provider.")

        yield from provider.generate_stream(
            GenerationRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content=request.prompt,
                    )
                ],
                config=GenerationConfig(
                    stream=True,
                ),
            )
        )