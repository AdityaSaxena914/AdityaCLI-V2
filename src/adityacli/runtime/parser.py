from __future__ import annotations

from .parser_models import RuntimePlan
from .parsers import (
    EditParser,
    GitParser,
    ReadParser,
    SearchParser,
    TerminalParser,
    WriteParser,
    DeleteParser,
    MoveParser,
    CopyParser,
)


class RuntimeParser:

    def __init__(self) -> None:
        self._parsers = {
            "read_file": ReadParser(),
            "write_file": WriteParser(),
            "edit_file": EditParser(),
            "delete_file": DeleteParser(),
            "move_file": MoveParser(),
            "copy_file": CopyParser(),
            "workspace_search": SearchParser(),
            "terminal": TerminalParser(),
            "git_status": GitParser(),
        }

    def parse(
        self,
        tool: str,
        prompt: str,
    ) -> RuntimePlan:
        parser = self._parsers.get(tool)

        if parser is None:
            return RuntimePlan()

        return parser.parse(prompt)