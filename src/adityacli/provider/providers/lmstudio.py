from __future__ import annotations

from collections.abc import Iterator

from ..interface import ProviderInterface
from ..models import (
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    ProviderInfo,
)

class LMStudioProvider(ProviderInterface):
    """LM Studio provider implementation."""
    def __init__(self) -> None:
        self._base_url = ""
        self._model = ""
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True
    
    def health_check(self) -> bool:
        return self._initialized
    
    def provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name="LM Studio",
            endpoint=self._base_url
        )
    
    def list_models(self) -> list[ModelInfo]:
        return []
    
    def load_model(self, model: str) -> None:
        self._model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise NotImplementedError
    
    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        raise NotImplementedError