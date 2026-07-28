from ddgs import DDGS

from core.models import SearchResult
from providers.base import SearchProvider


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider."""

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []

        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", ""),
                        body=item.get("body", ""),
                    )
                )

        return results