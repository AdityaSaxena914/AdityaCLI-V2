from __future__ import annotations

from abc import ABC, abstractmethod

from adityacli.core.models import Command, ToolResult


class BaseTool(ABC):
    """
    Base class for all deterministic tools.

    Tools perform deterministic work only.
    They never communicate with the LLM.
    They return structured data for the Runtime.
    """

    @abstractmethod
    def execute(self, command: Command) -> ToolResult:
        """
        Execute the tool.

        Returns:
            ToolResult containing the prompt for the LLM and structured
            metadata for the Runtime.
        """
        raise NotImplementedError