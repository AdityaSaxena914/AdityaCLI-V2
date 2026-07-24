from __future__ import annotations

from adityacli.contracts.tools import (
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
)

from .registry import ToolRegistry


class ToolManager:
    """Manage tool execution."""

    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:
        self._registry = registry

    def execute(
        self,
        name: str,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        tool = self._registry.create(name)
        return tool.execute(request)

    def definition(
        self,
        name: str,
    ) -> ToolDefinition:
        return self._registry.definition(name)

    def definitions(
        self,
    ) -> list[ToolDefinition]:
        return self._registry.definitions()

    def exists(
        self,
        name: str,
    ) -> bool:
        return self._registry.exists(name)