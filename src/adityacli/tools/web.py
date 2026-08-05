from __future__ import annotations
from typing import override
from adityacli.config import AppConfig
from adityacli.providers.base import SearchProvider
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import InvalidSyntaxError
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

    @override
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

        if self._provider is None:
            raise RuntimeError(
                "No search provider configured."
            )
        results = self._provider.search(query)

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

            prompt = (
                load_prompt("web")
                + "\n\n"
                + "\n".join(sections)
            )

        else:
            urls = []

            prompt = (
                f'No web results found for "{query}".'
            )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                web_urls=tuple(urls),
                extra={
                    "query": query,
                    "result_count": len(results),
                },
            ),
        )