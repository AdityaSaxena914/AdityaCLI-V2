from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    AgentInfo,
    AgentRequest,
    AgentResponse,
)

class AgentInterface(ABC):
    """Contract implemented by every agent."""

    @abstractmethod
    def info(self) -> AgentInfo:
        """Return agent metadata."""
        ...
    
    @abstractmethod
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        """Execute the agent."""
        ...