from __future__ import annotations

from collections.abc import Iterator

from adityacli.contracts.chat import ChatMessage
from adityacli.contracts.generation import (
    GenerationConfig,
    GenerationRequest,
)
from adityacli.contracts.tool_context import ToolExecutionContext
from adityacli.contracts.tools import ToolExecutionRequest
from adityacli.provider import ProviderManager
from adityacli.security import SecurityManager
from adityacli.tool.manager import ToolManager
from adityacli.workspace import WorkspaceManager

from ..interface import AgentInterface
from ..models import (
    AgentInfo,
    AgentRequest,
    AgentResponse,
)
from adityacli.conversation.manager import ConversationManager
from ..message_builder import MessageBuilder

class DefaultAgent(AgentInterface):
    """Default agent implementation."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
        workspace_manager: WorkspaceManager,
        security_manager: SecurityManager,
        conversation_manager: ConversationManager,
    ) -> None:
        self._provider_manager = provider_manager
        self._tool_manager = tool_manager
        self._workspace_manager = workspace_manager
        self._security_manager = security_manager

        self._message_builder = MessageBuilder(
            conversation_manager,
        )

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

        messages = self._message_builder.build(
            system_prompt=request.system_prompt,
            user_prompt=request.prompt,
        )

        response = provider.generate(
            GenerationRequest(
                messages=messages,
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(),
            )
        )

        assistant_message = response.message

        if not assistant_message.tool_calls:
            return AgentResponse(
                response=assistant_message.content or "",
            )

        messages.append(assistant_message)

        for call in assistant_message.tool_calls:

            tool_request = ToolExecutionRequest(
                arguments=call.arguments,
                context=ToolExecutionContext(
                    workspace_manager=self._workspace_manager,
                    security_manager=self._security_manager,
                ),
            )

            result = self._tool_manager.execute(
                call.name,
                tool_request,
            )

            messages.append(
                ChatMessage(
                    role="tool",
                    tool_call_id=call.id,
                    name=call.name,
                    content=result.content,
                )
            )

        final_response = provider.generate(
            GenerationRequest(
                messages=messages,
                config=GenerationConfig(),
            )
        )

        return AgentResponse(
            response=final_response.message.content or "",
        )

    def execute_stream(
        self,
        request: AgentRequest,
    ) -> Iterator[str]:
        """Execute the agent with streaming."""

        provider = self._provider_manager.active_provider

        if provider is None:
            raise RuntimeError("No active provider.")

        messages = self._message_builder.build(
            system_prompt=request.system_prompt,
            user_prompt=request.prompt,
        )
        

        response = provider.generate(
            GenerationRequest(
                messages=messages,
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(),
            )
        )

        assistant_message = response.message

        if assistant_message.tool_calls:

            messages.append(assistant_message)

            for call in assistant_message.tool_calls:

                tool_request = ToolExecutionRequest(
                    arguments=call.arguments,
                    context=ToolExecutionContext(
                        workspace_manager=self._workspace_manager,
                        security_manager=self._security_manager,
                    ),
                )

                result = self._tool_manager.execute(
                    call.name,
                    tool_request,
                )

                messages.append(
                    ChatMessage(
                        role="tool",
                        tool_call_id=call.id,
                        name=call.name,
                        content=result.content,
                    )
                )

            yield from provider.generate_stream(
                GenerationRequest(
                    messages=messages,
                    config=GenerationConfig(
                        stream=True,
                    ),
                )
            )

            return


        yield from provider.generate_stream(
            GenerationRequest(
                messages=messages,
                tools=self._tool_manager.definitions(),
                config=GenerationConfig(
                    stream=True,
                ),
            )
        )