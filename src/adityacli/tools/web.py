from __future__ import annotations
from typing import override
import threading
from adityacli.core.operations import bounded_tool, current_operation
from adityacli.config import AppConfig
from adityacli.providers.base import SearchProvider
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import InvalidSyntaxError, ToolExecutionError
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt


class WebTool(BaseTool):
    """Collect web information using the configured provider."""

    def __init__(
        self,
        config: AppConfig,
        provider: SearchProvider | None,
    ) -> None:
        self._config: AppConfig = config
        self._provider: SearchProvider | None = provider
        self._provider_lock = threading.Lock()

    @override
    @bounded_tool
    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        if not command.arguments:
            raise InvalidSyntaxError(
                "Expected a search query."
            )

        query = " ".join(command.arguments).strip()

        if not query:
            raise InvalidSyntaxError(
                "Expected a search query."
            )
        if len(query) > self._config.execution.max_query_chars:
            raise InvalidSyntaxError("Web query exceeds its size limit.")

        if self._provider is None:
            raise RuntimeError(
                "No search provider configured."
            )
        if not self._provider_lock.acquire(blocking=False):
            raise ToolExecutionError("The previous search provider request is still closing.")
        def retrieve():
            try:
                return self._provider.search(query)
            finally:
                self._provider_lock.release()
        operation = current_operation()
        assert operation is not None
        results = operation.run_io(retrieve, interrupt=lambda: None)
        if not isinstance(results, list):
            raise ToolExecutionError("Search provider returned an invalid result list.")
        results = results[:5]
        for result in results:
            if not all(isinstance(getattr(result, key, None), str) for key in ("title", "url", "body")):
                raise ToolExecutionError("Search provider returned an invalid record.")
            if sum(len(getattr(result, key).encode("utf-8")) for key in ("title", "url", "body")) > 32768:
                raise ToolExecutionError("Search provider record exceeds its byte limit.")

        if results:
            sections = [
                "===== BEGIN UNTRUSTED WEB DATA =====",
                f'Web search results for "{query}":',
                "",
            ]

            urls: list[str] = []

            for result in results:
                urls.append(result.url)

                sections.extend(
                    [
                        f"Title: {result.title}",
                        f"URL: {result.url}",
                        result.body,
                        "",
                    ]
                )

            sections.append("===== END UNTRUSTED WEB DATA =====")

            prompt = "\n".join(sections)

        else:
            urls = []

            prompt = (
                f'No web results found for "{query}".'
            )

        if command.prompt:
            prompt += "\n\n=== USER REQUEST ===\n" + command.prompt

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                web_urls=tuple(urls),
                extra={
                    "query": query,
                    "result_count": len(results),
                    "instructions": load_prompt("web"),
                },
            ),
        )
