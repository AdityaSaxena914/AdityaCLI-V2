from pathlib import Path

from config import AppConfig
from core.models import Command
from exceptions import InvalidSyntaxError
from tools.base import BaseTool


class SearchTool(BaseTool):
    """Search tool."""

    @property
    def name(self) -> str:
        return "search"

    def execute(self, command: Command) -> str:
        if len(command.arguments) != 1:
            raise InvalidSyntaxError("Expected exactly one search query.")

        query = command.arguments[0]
        workspace = self._config.workspace.root.resolve()

        matches: list[str] = []

        for path in workspace.rglob("*"):
            if not path.is_file():
                continue

            try:
                with path.open(
                    "r",
                    encoding=self._config.workspace.encoding,
                ) as file:
                    for line_number, line in enumerate(file, start=1):
                        if query in line:
                            matches.append(
                                f"{path.relative_to(workspace)}:{line_number}: {line.rstrip()}"
                            )
            except (UnicodeDecodeError, OSError):
                continue

        if not matches:
            context = "No matches found."
        else:
            context = "\n".join(matches)

        return (
            f"Search Query: {query}\n\n"
            f"Search Results:\n{context}\n\n"
            f"User Request:\n{command.prompt}"
        )
