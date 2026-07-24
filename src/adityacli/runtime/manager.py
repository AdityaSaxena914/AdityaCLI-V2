from __future__ import annotations

from pathlib import Path
from collections.abc import Iterator
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
from .exceptions import PipelineDispatchError
from .context_builder import ContextBuilder
from .intent_router import IntentRouter
from .pipeline_dispatcher import PipelineDispatcher
from .prompt_manager import PromptManager
from .resource_manager import ResourceManager
from .models import (
    IntentResult,
    IntentType,
    PipelineType,
    RuntimeResponse,
)
from .parser import RuntimeParser
from adityacli.conversation.manager import ConversationManager
from .path_extractor import PathExtractor

class RuntimeManager:
    """Runtime-first execution manager."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
        workspace_manager: WorkspaceManager,
        security_manager: SecurityManager,
        agent_manager: AgentManager,
        conversation_manager: ConversationManager,
    ) -> None:

        self._provider_manager = provider_manager
        self._tool_manager = tool_manager
        self._workspace_manager = workspace_manager
        self._security_manager = security_manager
        self._agent_manager = agent_manager
        self._conversation_manager = conversation_manager

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
        self._path_extractor = PathExtractor()

        self._tool_context: ToolExecutionContext = ToolExecutionContext(
            workspace_manager=self._workspace_manager,
            security_manager=self._security_manager,
        )

        
    def execute(
        self,
        prompt: str,
    ) -> RuntimeResponse:
        """Compatibility wrapper around execute_stream()."""

        return RuntimeResponse(
            content="".join(
                self.execute_stream(prompt)
            )
        )


    def execute_stream(
        self,
        prompt: str,
    ) -> Iterator[str]:
        """Execute a user request as a stream."""

        self._resource_manager.validate()

        intent = self._intent_router.route(prompt)

        

        pipeline = self._pipeline_dispatcher.dispatch(
            intent,
        )

        if pipeline is PipelineType.DETERMINISTIC:
            yield from self._execute_deterministic_stream(
                prompt,
                intent.tool_name,
                intent.intent,
            )
            return

        yield from self._execute_agent_stream(prompt,pipeline,intent)



    def _execute_agent_stream(
        self,
        prompt: str,
        pipeline: PipelineType,
        intent: IntentResult,
    ) -> Iterator[str]:
        """Stream semantic/reasoning execution."""

        context = None

        if pipeline in (
            PipelineType.SEMANTIC,
            PipelineType.REASONING,
        ):
            path = self._path_extractor.extract(prompt)

            if path is not None:
                plan = self._parser.parse(
                    "read_file",
                    f"read {path.as_posix()}",
                )

                if not plan.empty:
                    context = self._context_builder.build(
                        plan=plan,
                        context_budget=self._resource_manager.context_budget(),
                    )
                

        prompt_context = self._prompt_manager.build(
            pipeline=pipeline,
            user_prompt=prompt,
            context=context,
        )

        self._conversation_manager.append_user(prompt)

        chunks: list[str] = []

        for chunk in self._agent_manager.execute_stream(
            AgentRequest(
                system_prompt=prompt_context.system_prompt,
                prompt=prompt_context.user_prompt,
            )
        ):
            chunks.append(chunk)
            yield chunk

        self._conversation_manager.append_assistant(
            "".join(chunks)
        )



    def _execute_deterministic_stream(
        self,
        prompt: str,
        tool_name: str | None,
        intent: IntentType,
    ) -> Iterator[str]:
        """Execute deterministic requests as a stream."""

        if tool_name is None:
            raise PipelineDispatchError(
                "Deterministic pipeline requires a tool."
            )

        plan = self._parser.parse(
            tool_name,
            prompt,
        )

        if plan.empty:
            yield "Nothing to execute."
            return

        first = True

        for step in plan.steps:

            result = self._tool_manager.execute(
                step.tool,
                ToolExecutionRequest(
                    arguments=step.arguments,
                    context=self._tool_context,
                ),
            )

            if not first:
                yield "\n"

            first = False

            yield result.content