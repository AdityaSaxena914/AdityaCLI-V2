from __future__ import annotations

from adityacli.provider import (
    ProviderManager,
    ProviderRegistry,
    LMStudioProvider,
)

class Application:
    """Application runtime."""
    def __init__(self) -> None:
        self._provider_registry = ProviderRegistry()
        self._provider_manager = ProviderManager(
            self._provider_registry
        )

    def register_provider(self) -> None:
        """Register built-in providers."""

        self._provider_registry.register(
            "lmstudio",
            LMStudioProvider,
        )

    def startup(self) -> None:
        """Start the application"""

        self.register_provider()

    def shutdown(self) -> None:
        """Shutdown the application."""

        if self._provider_manager.active_provider is not None:
            self._provider_manager.active_provider.shutdown()