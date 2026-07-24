from __future__ import annotations

from collections.abc import Iterator
from adityacli.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)
from adityacli.contracts.provider import (
    ModelInfo,
    ProviderInfo,
)

from .interface import ProviderInterface
from .registry import ProviderRegistry


class ProviderManager:
    """Manage provider lifecycle and active provider."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._active_provider: ProviderInterface | None = None

    @property
    def provider(self) -> ProviderInterface:
        """Return the active provider."""

        if self._active_provider is None:
            raise RuntimeError("No active provider.")

        return self._active_provider

    @property
    def active_provider(self) -> ProviderInterface | None:
        """
        Backward-compatible accessor.

        Returns None when no provider is active.
        """

        return self._active_provider


    def switch_provider(self, name: str) -> None:
        """Switch the active provider."""

        if self._active_provider is not None:
            self._active_provider.shutdown()

        provider = self._registry.create(name)

        provider.initialize()

        self._active_provider = provider

    def health_check(self) -> bool:
        """Return whether the active provider is healthy."""

        if self._active_provider is None:
            return False

        return self.provider.health_check()

    def provider_info(self) -> ProviderInfo:
        """Return information about the active provider."""

        return self.provider.provider_info()

    def list_models(self) -> list[ModelInfo]:
        return self.provider.list_models()


    def model_info(self) -> ModelInfo:
        return self.provider.model_info()


    def load_model(self, model: str) -> None:
        self.provider.load_model(model)


    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        return self.provider.generate(request)


    def generate_stream(
        self,
        request: GenerationRequest,
    ) -> Iterator[str]:
        yield from self.provider.generate_stream(request)