from __future__ import annotations
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import InvalidSyntaxError
from adityacli.tools.base import BaseTool


class SearchTool(BaseTool):
    """Deterministically search the workspace."""
    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        self._config = config

    def execute(self, command: Command) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidSyntaxError(
                "Expected exactly one search query."
            )

        query = command.arguments[0]
        workspace = self._config.workspace.root.resolve()

        matches: list[str] = []

        for path in workspace.rglob("*"):
            if not path.is_file():
                continue

            try:
                content = path.read_text(
                    encoding=self._config.workspace.encoding,
                )
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(
                content.splitlines(),
                start=1,
            ):
                if query in line:
                    relative = path.relative_to(workspace)

                    matches.append(
                        f"{relative}:{line_number}: {line}"
                    )

        if matches:
            prompt = (
                f'Search results for "{query}":\n\n'
                + "\n".join(matches)
            )
        else:
            prompt = (
                f'No matches found for "{query}".'
            )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                search_results=tuple(matches),
                extra={
                    "query": query,
                    "match_count": len(matches),
                },
            ),
            requires_llm=False,
        )