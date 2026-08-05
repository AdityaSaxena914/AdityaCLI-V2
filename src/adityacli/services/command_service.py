from __future__ import annotations

from adityacli.core.models import Command, ToolResult, Tool
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
        self._parser: Parser = parser
        self._registry: ToolRegistry = registry

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

    def needs_followup(
        self,
        text: str,
    ) -> str | None:
        command = self.parse(text)

        if command is None:
            return None

        if command.tool is Tool.WRITE and "\n" not in text:
            return "What would you like to generate?"

        if command.tool is Tool.EDIT and "\n" not in text:
            return "What would you like to change?"

        return None