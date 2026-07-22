from __future__ import annotations
from adityacli.contracts.chat import ChatMessage
from adityacli.contracts.generation import GenerationConfig, GenerationRequest
from adityacli.contracts.tools import ToolExecutionRequest
from adityacli.provider import ProviderManager
from collections.abc import Iterator
from ..interface import AgentInterface
from ..models import (
    AgentInfo,
    AgentRequest,
    AgentResponse,
)
from adityacli.tool.manager import ToolManager


class DefaultAgent(AgentInterface):
    """Default agent implementation."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
    ):
        self._provider_manager = provider_manager
        self._tool_manager = tool_manager


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
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(),
            )
        )

        print("Tool calls:", response.message.tool_calls)

        if not response.message.tool_calls:
            return AgentResponse(
                response=response.message.content,
            )
        
        messages = [
            ChatMessage(
                role="user",
                content=request.prompt,
            )
        ]

        for call in response.message.tool_calls:

            result = self._tool_manager.execute(
                call.name,
                ToolExecutionRequest(
                    arguments=call.arguments,
                ),
            )

            print(result)

            messages.append(
                ChatMessage(
                    role="tool",
                    tool_call_id=call.id,
                    name=call.name,
                    content=result.content,
                )
            )

        final = provider.generate(
            GenerationRequest(
                messages=messages,
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(),
            )
        )

        return AgentResponse(
            response=final.message.content,
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
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(
                    stream=True,
                ),
            )
        )