from abc import ABC, abstractmethod

from core.models import SearchResult


class SearchProvider(ABC):
    """Base search provider."""

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        ...