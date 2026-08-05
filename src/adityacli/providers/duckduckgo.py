from collections.abc import Iterable
from typing import Protocol, override, cast
from ddgs import DDGS  # pyright: ignore[reportUnknownVariableType]
from adityacli.core.models import SearchResult
from adityacli.providers.base import SearchProvider

class DDGSResult(Protocol):
    def get(
        self,
        key: str,
        default: str = "",
    ) -> str: ...


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider."""

    @override
    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []

        with DDGS() as ddgs:  # pyright: ignore[reportAny]
            items = cast(
                Iterable[DDGSResult],
                ddgs.text( # pyright: ignore[reportAny]
                    query,
                    max_results=max_results,
                ),
            )

            for item in items:
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", ""),
                        body=item.get("body", ""),
                    )
                )

        return results