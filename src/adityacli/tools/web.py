from config import AppConfig
from core.models import Command
from providers.base import SearchProvider
from providers.duckduckgo import DuckDuckGoProvider
from tools.base import BaseTool


class WebTool(BaseTool):
    """Web tool."""

    def __init__(
        self,
        config: AppConfig,
        provider: SearchProvider | None = None,
    ) -> None:
        super().__init__(config)
        self._provider = provider or DuckDuckGoProvider()

    @property
    def name(self) -> str:
        return "web"

    def execute(self, command: Command) -> str:
        query = " ".join(command.arguments)

        if command.prompt:
            query = f"{query}\n{command.prompt}".strip()

        results = self._provider.search(query)

        if not results:
            return (
                f"Search Query:\n{query}\n\n"
                "No search results were found."
            )

        prompt = [
            f"Search Query:\n{query}\n",
            "Search Results:\n",
        ]

        for index, result in enumerate(results, start=1):
            prompt.append(
                f"{index}.\n"
                f"Title: {result.title}\n"
                f"URL: {result.url}\n"
                f"Body: {result.body}\n"
            )

        prompt.append(
            "\nUse the search results above to answer the user's request."
        )

        return "\n".join(prompt)