from __future__ import annotations

from pathlib import Path

from adityacli.contracts.chat import ChatMessage
from adityacli.contracts.generation import (
    GenerationConfig,
    GenerationRequest,
)
from adityacli.provider import ProviderManager
from adityacli.tool import ToolManager
from adityacli.workspace import WorkspaceManager

from .context_builder import ContextBuilder
from .intent_router import IntentRouter
from .pipeline_dispatcher import PipelineDispatcher
from .prompt_manager import PromptManager
from .resource_manager import ResourceManager
from .models import RuntimeResponse, PipelineType


class RuntimeManager:
    """Runtime Intelligence engine."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self._provider = provider_manager
        self._tools = tool_manager
        self._workspace = workspace_manager

        self._resources = ResourceManager(
            provider_manager,
        )

        self._router = IntentRouter()

        self._dispatcher = PipelineDispatcher()

        self._context_builder = ContextBuilder(
            workspace_manager,
        )

        self._prompt_builder = PromptManager()

    def execute(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Execute a user request."""

        self._resources.validate()

        intent = self._router.route(prompt)

        pipeline = self._dispatcher.dispatch(intent)

        match pipeline:

            case PipelineType.DETERMINISTIC:
                return self._execute_deterministic(
                    prompt,
                    intent.tool,
                )

            case PipelineType.SEMANTIC:
                return self._execute_semantic(
                    prompt,
                )

            case PipelineType.REASONING:
                return self._execute_reasoning(
                    prompt,
                )

            case PipelineType.AMBIGUOUS:
                return RuntimeResponse(
                    content=(
                        "Your request is ambiguous. "
                        "Please clarify."
                    )
                )

        raise RuntimeError("Unknown pipeline.")

    def _execute_deterministic(
        self,
        prompt: str,
        tool: str | None,
    ) -> RuntimeResponse:
        """Execute deterministic requests."""

        raise NotImplementedError()

    def _execute_semantic(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Execute semantic requests."""

        prompt_context = self._prompt_builder.build(
            pipeline=PipelineType.SEMANTIC,
            user_prompt=prompt,
        )

        request = GenerationRequest(
            messages=[
                ChatMessage(
                    role="system",
                    content=prompt_context.system_prompt,
                ),
                ChatMessage(
                    role="user",
                    content=prompt_context.user_prompt,
                ),
            ],
            config=GenerationConfig(),
        )

        response = self._provider.generate(
            request,
        )

        return RuntimeResponse(
            content=response.message.content,
        )

    def _execute_reasoning(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Execute reasoning requests."""

        prompt_context = self._prompt_builder.build(
            pipeline=PipelineType.REASONING,
            user_prompt=prompt,
        )

        request = GenerationRequest(
            messages=[
                ChatMessage(
                    role="system",
                    content=prompt_context.system_prompt,
                ),
                ChatMessage(
                    role="user",
                    content=prompt_context.user_prompt,
                ),
            ],
            config=GenerationConfig(),
        )

        response = self._provider.generate(
            request,
        )

        return RuntimeResponse(
            content=response.message.content,
        )