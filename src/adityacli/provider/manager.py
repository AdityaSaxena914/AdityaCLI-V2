from __future__ import annotations

from .interface import ProviderInterface
from .registry import ProviderRegistry

class ProviderManager:
    """Manage provider lifecycle and active provider."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._active_provider: ProviderInterface | None = None

    @property
    def active_provider(self) -> ProviderInterface | None:
        """Return the active provider."""

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
        
        return self._active_provider.health_check()
    
    def load_model(self, model: str) -> None:
        """Load a model into the active provider."""

        if self._active_provider is None:
            raise RuntimeError("No active provider.")
        
        self._active_provider.load_model(model)