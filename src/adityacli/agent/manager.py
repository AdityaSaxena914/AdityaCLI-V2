from __future__ import annotations
from adityacli.provider import ProviderManager
from adityacli.security import SecurityManager
from adityacli.session import SessionManager
from adityacli.tool import ToolManager
from adityacli.workspace import WorkspaceManager
from collections.abc import Iterator
from .interface import AgentInterface
from .models import (
    AgentRequest,
    AgentResponse,
)
from .exceptions import AgentNotAvailableError

class AgentManager:
    """Manage agent execution."""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tool_manager: ToolManager,
        workspace_manager: WorkspaceManager,
        session_manager: SessionManager,
        security_manager: SecurityManager,
    ) -> None:
        self._provider_manager = provider_manager
        self._tool_manager = tool_manager
        self._workspace_manager = workspace_manager
        self._session_manager = session_manager
        self._security_manager = security_manager

        self._agent: AgentInterface | None = None

    @property
    def agent(self) -> AgentInterface | None:
        """Return the active agent."""

        return self._agent
    

    def set_agent(
        self,
        agent: AgentInterface,
    ) -> None:
        """Set the active agent."""

        self._agent = agent

    
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        """Execute the active agent."""

        if self._agent is None:
            raise AgentNotAvailableError(
                "No active agent."
            )
        return self._agent.execute(request)
    
    def execute_stream(
        self,
        request: AgentRequest,
    ) -> Iterator[str]:
        """Execute the active agent with streaming."""

        if self._agent is None:
            raise AgentNotAvailableError(
                "No active agent."
            )
        return self._agent.execute_stream(request)