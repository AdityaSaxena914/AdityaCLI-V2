from __future__ import annotations

import re
import shutil
import json
import sys
from collections.abc import Iterator
from contextlib import closing
from itertools import islice
from pathlib import Path
from typing import override

from adityacli.config import AppConfig
from adityacli.core.models import Command, ToolMetadata, ToolResult
from adityacli.core.path_resolver import PathResolver
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.core.processes import ProcessOutput, find_executable
from adityacli.core.operations import bounded_tool
from adityacli.exceptions import InvalidPathError, InvalidSyntaxError, ToolExecutionError
from adityacli.tools.base import BaseTool


MAX_RESULTS = 50
MAX_COLUMNS = 300


class SearchTool(BaseTool):
    """Pruned filename lookup followed by streaming, bounded code search."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._guard = WorkspaceGuard(config)
        self._resolver = PathResolver(config)

    @override
    @bounded_tool
    def execute(self, command: Command) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidSyntaxError("Expected exactly one search query.")
        query = command.arguments[0]
        if len(query) > self._config.execution.max_query_chars:
            raise InvalidSyntaxError("Search query exceeds its size limit.")
        literal = query.startswith("--literal ")
        if literal:
            query = query[len("--literal "):]
            if not query:
                raise InvalidSyntaxError("Literal search requires a nonempty query.")
        # Search queries are text, not paths; validate filename lookups only
        # when they are bare names, allowing regex content patterns.
        filenames = []
        if not any(character in query for character in ("/", "\\", ":")):
            filenames = self._resolver.find_by_name(query, limit=MAX_RESULTS + 1)
        if filenames:
            matches = [str(path.relative_to(self._guard.workspace)) for path in filenames]
        else:
            backend = self._ripgrep if shutil.which("rg") and find_executable("rg", self._guard.workspace) else self._python_search
            with closing(backend(query, literal=literal)) as results:
                matches = list(islice(results, MAX_RESULTS + 1))
        truncated = len(matches) > MAX_RESULTS
        matches = matches[:MAX_RESULTS]
        lines = list(matches)
        if truncated:
            lines.append("... additional matches omitted (50-result limit).")
        prompt = f'Search results for "{query}":\n\n' + "\n".join(lines) if matches else f'No matches found for "{query}".'
        return ToolResult(prompt, ToolMetadata(
            search_results=tuple(matches),
            extra={"query": query, "match_count": len(matches), "truncated": truncated},
        ), requires_llm=False)

    def _batches(self) -> Iterator[list[str]]:
        batch: list[str] = []
        length = 0
        for path in self._guard.iter_files(max_size=True):
            relative = str(path.relative_to(self._guard.workspace))
            self._guard.existing_file(relative)
            if batch and (len(batch) >= 64 or length + len(relative) > 12000):
                yield batch
                batch, length = [], 0
            batch.append(relative)
            length += len(relative) + 3
        if batch:
            yield batch

    def _ripgrep(self, query: str, *, literal: bool = False) -> Iterator[str]:
        for batch in self._batches():
            args = [
                "rg", "--no-config", "--no-ignore", "--no-ignore-parent", "--no-ignore-global",
                "--line-number", "--with-filename", "--smart-case", "--color=never",
                "--max-count", str(MAX_RESULTS + 1), "--max-columns", str(MAX_COLUMNS),
                "--max-columns-preview", "--max-filesize", str(self._config.workspace.max_file_size),
                *(["--fixed-strings"] if literal else []),
                "-e", query, "--", *batch,
            ]
            try:
                process = ProcessOutput(args, cwd=self._guard.workspace, timeout=self._config.execution.tool_timeout)
                with closing(iter(process)) as chunks:
                    errors = []
                    pending = b""
                    for chunk in chunks:
                        pending += chunk
                        lines = pending.split(b"\n")
                        pending = lines.pop()
                        if len(pending) > 65536:
                            raise ToolExecutionError("Search output line exceeds its limit.")
                        for raw in lines:
                            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                            if re.match(r"^.+:\d+:", line):
                                yield line
                            elif line and len(errors) < 4:
                                errors.append(line)
                    if pending:
                        errors.append(pending.decode("utf-8", errors="replace"))
                    if process.returncode not in (0, 1):
                        raise ToolExecutionError("\n".join(errors) or f"ripgrep exited with code {process.returncode}.")
            except OSError as exc:
                raise ToolExecutionError(f"Failed to execute ripgrep: {exc}") from exc

    def _python_search(self, query: str, *, literal: bool = False) -> Iterator[str]:
        request = json.dumps({"workspace": str(self._guard.workspace), "query": query,
                              "literal": literal,
                              "encoding": self._config.workspace.encoding,
                              "max_file_size": self._config.workspace.max_file_size}).encode("utf-8")
        process = ProcessOutput([sys.executable, "-I", str(Path(__file__).with_name("_search_worker.py"))],
                                cwd=self._guard.workspace, timeout=self._config.execution.regex_timeout,
                                input_bytes=request)
        pending = b""
        with closing(iter(process)) as chunks:
            for chunk in chunks:
                pending += chunk
                lines = pending.split(b"\n")
                pending = lines.pop()
                if len(pending) > 65536:
                    raise ToolExecutionError("Fallback search returned an oversized record.")
                for line in lines:
                    try:
                        record = json.loads(line)
                    except ValueError as exc:
                        raise ToolExecutionError("Fallback search worker failed.") from exc
                    if "error" in record:
                        raise InvalidSyntaxError(record["error"])
                    yield record["match"]
        if process.returncode or pending:
            raise ToolExecutionError("Fallback search worker failed.")
