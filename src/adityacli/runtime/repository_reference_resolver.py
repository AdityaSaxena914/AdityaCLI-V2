from __future__ import annotations

from pydantic import BaseModel

from adityacli.repository import (
    RepositoryManager,
    SymbolExtractor,
)
from adityacli.repository.models import RepositoryReference
from adityacli.repository.query_type import RepositoryQueryType


class RepositoryResolution(BaseModel):
    query: RepositoryQueryType | None
    target: str
    references: list[RepositoryReference]


class RepositoryReferenceResolver:
    """Resolve repository references from a user prompt."""

    def __init__(
        self,
        repository: RepositoryManager,
    ) -> None:
        self._repository = repository
        self._symbols = SymbolExtractor()

    def resolve(
        self,
        prompt: str,
    ) -> RepositoryResolution:

        symbol = self._symbols.extract(prompt)

        if symbol is None:
            return RepositoryResolution(
                query=None,
                target="",
                references=[],
            )

        text = prompt.lower()

        if any(
            phrase in text
            for phrase in (
                "who calls",
                "where is",
                "where's",
                "callers",
                "used by",
            )
        ):
            return RepositoryResolution(
                query=RepositoryQueryType.CALLERS,
                target=symbol,
                references=self._repository.resolve_callers(symbol),
            )

        reference = self._repository.resolve_symbol(symbol)

        return RepositoryResolution(
            query=RepositoryQueryType.SYMBOL,
            target=symbol,
            references=[] if reference is None else [reference],
        )