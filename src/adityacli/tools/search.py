from __future__ import annotations

from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import InvalidSyntaxError
from adityacli.tools.base import BaseTool


_IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    ".sessions",
}

_IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
}


class SearchTool(BaseTool):
    """Deterministically search the workspace."""

    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        self._config = config

    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidSyntaxError(
                "Expected exactly one search query."
            )

        query = command.arguments[0]
        query_lower = query.lower()

        workspace = self._config.workspace.root.resolve()

        # ------------------------------------------------------------------
        # Filename search
        # ------------------------------------------------------------------

        filename_matches: list[str] = []

        for path in workspace.rglob("*"):
            if any(
                part in _IGNORE_DIRS
                for part in path.parts
            ):
                continue

            if not path.is_file():
                continue

            stem = path.stem.lower()
            name = path.name.lower()

            if (
                query_lower == stem
                or query_lower == name
            ):
                filename_matches.append(
                    str(path.relative_to(workspace))
                )

        if filename_matches:
            return ToolResult(
                prompt="\n".join(filename_matches),
                metadata=ToolMetadata(
                    search_results=tuple(filename_matches),
                    extra={
                        "query": query,
                        "match_count": len(filename_matches),
                    },
                ),
                requires_llm=False,
            )

        # ------------------------------------------------------------------
        # Content search
        # ------------------------------------------------------------------

        matches: list[str] = []

        for path in workspace.rglob("*"):
            if any(
                part in _IGNORE_DIRS
                for part in path.parts
            ):
                continue

            if not path.is_file():
                continue

            if path.suffix in _IGNORE_SUFFIXES:
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
                if query_lower in line.lower():
                    matches.append(
                        f"{path.relative_to(workspace)}:{line_number}: {line}"
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