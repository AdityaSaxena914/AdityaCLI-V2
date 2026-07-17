from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
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

    @abstractmethod
    def execute_stream(
        self,
        request: AgentRequest,
    ) -> Iterator[str]:
        """Execute the agent with streaming."""
        ...