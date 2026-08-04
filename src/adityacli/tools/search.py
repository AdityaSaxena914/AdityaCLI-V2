from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import (
    InvalidSyntaxError,
    ToolExecutionError,
)
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

_MAX_RESULTS = 50


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

        filename_matches = self._filename_search(query)

        if filename_matches:
            matches = filename_matches
        elif shutil.which("rg") is not None:
            matches = self._ripgrep(query)
        else:
            matches = self._python_search(query)

        actual_match_count = len(matches)

        if actual_match_count > _MAX_RESULTS:
            truncated = actual_match_count - _MAX_RESULTS
            matches = matches[:_MAX_RESULTS]
        
            matches.append("")
            matches.append(
                f"... {truncated} additional matches omitted."
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
                    "match_count": actual_match_count,
                },
            ),
            requires_llm=False,
        )


    def _filename_search(
        self,
        query: str,
    ) -> list[str]:
        workspace = self._config.workspace.root.resolve()

        query_lower = query.lower()

        matches: list[str] = []

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
                matches.append(
                    str(path.relative_to(workspace))
                )

        return matches


    def _ripgrep(
        self,
        query: str,
    ) -> list[str]:
        """
        Search using ripgrep.
        """

        workspace = self._config.workspace.root.resolve()

        command = [
            "rg",
            "--line-number",
            "--with-filename",
            "--smart-case",
            "--hidden",
            "--color=never",
            "--max-count",
            str(_MAX_RESULTS + 1),

            "--glob", "!*.pyc",
            "--glob", "!*.pyo",

            query,
            str(workspace),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to execute ripgrep: {exc}"
            ) from exc

        if result.returncode not in (0, 1):
            raise ToolExecutionError(
                result.stderr.strip()
            )

        matches: list[str] = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            prefix = str(workspace) + "/"

            if line.startswith(prefix):
                line = line[len(prefix):]

            matches.append(line)

        return matches


    def _python_search(
        self,
        query: str,
    ) -> list[str]:
        """
        Fallback search when ripgrep is unavailable.
        """

        workspace = self._config.workspace.root.resolve()
        query_lower = query.lower()

        filename_matches: list[str] = []
        content_matches: list[str] = []

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

            stem = path.stem.lower()
            name = path.name.lower()

            if (
                query_lower == stem
                or query_lower == name
            ):
                filename_matches.append(
                    str(path.relative_to(workspace))
                )
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
                    content_matches.append(
                        f"{path.relative_to(workspace)}:{line_number}: {line}"
                    )

        if filename_matches:
            return filename_matches

        return content_matches