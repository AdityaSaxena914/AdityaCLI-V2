from __future__ import annotations

from collections.abc import Iterable

from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    Tool,
    ToolResult,
)
from adityacli.exceptions import InvalidCommandError
from adityacli.providers.base import SearchProvider
from adityacli.tools.base import BaseTool
from adityacli.tools.edit import EditTool
from adityacli.tools.git import GitTool
from adityacli.tools.read import ReadTool
from adityacli.tools.search import SearchTool
from adityacli.tools.web import WebTool
from adityacli.tools.write import WriteTool


class ToolRegistry:
    """Registry for deterministic tool dispatch."""

    def __init__(
        self,
        config: AppConfig,
        search_provider: SearchProvider | None = None,
    ) -> None:
        self._tools: dict[Tool, BaseTool] = {
            Tool.READ: ReadTool(config),
            Tool.WRITE: WriteTool(config),
            Tool.EDIT: EditTool(config),
            Tool.SEARCH: SearchTool(config),
            Tool.WEB: WebTool(
                config=config,
                provider=search_provider,
            ),
            Tool.GIT: GitTool(config),
        }

    def get(
        self,
        tool: Tool,
    ) -> BaseTool:
        try:
            return self._tools[tool]
        except KeyError as exc:
            name = getattr(tool, "value", str(tool))

            raise InvalidCommandError(
                f"Unsupported tool: {name}"
            ) from exc

    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        """
        Execute a deterministic tool.

        Runtime receives structured output instead of raw prompt text.
        """

        return self.get(command.tool).execute(command)

    def __contains__(
        self,
        tool: Tool,
    ) -> bool:
        return tool in self._tools

    def __iter__(self) -> Iterable[BaseTool]:
        return iter(self._tools.values())