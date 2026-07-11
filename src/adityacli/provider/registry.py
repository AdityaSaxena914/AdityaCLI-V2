from __future__ import annotations

from .interface import ProviderInterface


class ProviderRegistry:
    """Registry of available provider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, type[ProviderInterface]] = {}
    
    def register(
            self,
            name: str,
            provider_class: type[ProviderInterface],
    ) -> None:
        """Register a provider implementation."""

        if name in self._providers:
            raise ValueError(f"Provider '{name}' is already registered.")
        
        self._providers[name] = provider_class

    def exists(self, name: str) -> bool:
        """Return whether a provider is registered"""

        return name in self._providers
    
    def create(self, name: str) -> ProviderInterface:
        """Create a provider instance."""

        if not self.exists(name):
            raise ValueError(f"Provider '{name}' is not registered.")
        
        provider_class = self._providers[name]

        return provider_class()