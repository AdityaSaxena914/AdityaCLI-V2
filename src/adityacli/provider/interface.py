from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from adityacli.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)
from adityacli.contracts.provider import (
    ModelInfo,
    ProviderInfo,
)


class ProviderInterface(ABC):
    """Contract implemented by every provider."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the provider."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return whether the provider is available."""

    @abstractmethod
    def provider_info(self) -> ProviderInfo:
        """Return provider information."""

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Return all available models."""

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Return information about the currently loaded model."""

    @abstractmethod
    def load_model(self, model: str) -> None:
        """Load or activate a model."""

    @abstractmethod
    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Generate a complete response."""

    @abstractmethod
    def generate_stream(
        self,
        request: GenerationRequest,
    ) -> Iterator[str]:
        """Generate a streamed response."""