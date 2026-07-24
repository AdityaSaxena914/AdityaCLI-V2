from __future__ import annotations

from pathlib import Path

from adityacli.agent import (
    AgentManager,
    AgentRequest,
)
from adityacli.contracts.tool_context import ToolExecutionContext
from adityacli.contracts.tools import ToolExecutionRequest
from adityacli.provider import ProviderManager
from adityacli.tool import ToolManager
from adityacli.workspace import WorkspaceManager
from adityacli.security import SecurityManager

from .context_builder import ContextBuilder
from .intent_router import IntentRouter
from .pipeline_dispatcher import PipelineDispatcher
from .prompt_manager import PromptManager
from .resource_manager import ResourceManager
from .models import (
    IntentType,
    PipelineType,
    RuntimeResponse,
)
from .parser import RuntimeParser

class RuntimeManager:
    """Runtime-first execution manager."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
        workspace_manager: WorkspaceManager,
        security_manager: SecurityManager,
        agent_manager: AgentManager,
    ) -> None:
        self._provider_manager = provider_manager
        self._tool_manager = tool_manager
        self._workspace_manager = workspace_manager
        self._security_manager = security_manager
        self._agent_manager = agent_manager

        self._resource_manager = ResourceManager(
            provider_manager,
        )

        self._intent_router = IntentRouter()

        self._pipeline_dispatcher = PipelineDispatcher()

        self._context_builder = ContextBuilder(
            workspace_manager,
        )

        self._prompt_manager = PromptManager()
        self._parser = RuntimeParser()

    def execute(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Execute a user request."""

        self._resource_manager.validate()

        intent = self._intent_router.route(prompt)

        pipeline = self._pipeline_dispatcher.dispatch(
            intent,
        )

        if pipeline is PipelineType.DETERMINISTIC:
            return self._execute_deterministic(
                prompt,
                intent.tool_name,
                intent.intent,
            )

        return self._execute_agent(prompt)

    def _execute_agent(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Forward semantic/reasoning requests to the default agent."""

        response = self._agent_manager.execute(
            AgentRequest(
                prompt=prompt,
            )
        )

        return RuntimeResponse(
            content=response.response,
        )

    def _execute_deterministic(
        self,
        prompt: str,
        tool_name: str | None,
        intent: IntentType,
    ) -> RuntimeResponse:
        """Execute deterministic requests."""

        if tool_name is None:
            return self._execute_agent(prompt)

        plan = self._parser.parse(
            tool_name,
            prompt,
        )

        if plan.empty:
            return RuntimeResponse(
                content="Nothing to execute.",
            )

        output: list[str] = []

        for step in plan.steps:

            result = self._tool_manager.execute(
                step.tool,
                ToolExecutionRequest(
                    arguments=step.arguments,
                    context=ToolExecutionContext(
                        workspace_manager=self._workspace_manager,
                        security_manager=self._security_manager,
                    ),
                ),
            )

            output.append(result.content)

        return RuntimeResponse(
            content="\n".join(output),
        )