from __future__ import annotations

from ..interface import AgentInterface
from ..models import (
    AgentInfo,
    AgentRequest,
    AgentResponse,
)

class DefaultAgent(AgentInterface):
    """Default agent implementation."""

    def info(self) -> AgentInfo:
        """Return agent metadata."""

        return AgentInfo(
            name="default",
            description="Default AdityaCLI agent.",
        )
    
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        """Execute the agent."""

        raise NotImplementedError
    
    