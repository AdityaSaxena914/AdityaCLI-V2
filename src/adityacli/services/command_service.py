from __future__ import annotations

from adityacli.core.models import Command, ToolResult
from adityacli.core.parser import Parser
from adityacli.tools.registry import ToolRegistry


class CommandService:
    """
    Parses, validates and executes deterministic commands.
    """

    def __init__(
        self,
        parser: Parser,
        registry: ToolRegistry,
    ) -> None:
        self._parser = parser
        self._registry = registry

    def parse(
        self,
        text: str,
    ) -> Command | None:
        command = self._parser.parse(text)

        if command is not None:
            self._parser.validate(command)

        return command

    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        return self._registry.execute(command)