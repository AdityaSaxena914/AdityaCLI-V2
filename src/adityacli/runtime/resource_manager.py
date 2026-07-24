from __future__ import annotations

from adityacli.contracts.provider import ModelInfo
from adityacli.provider import ProviderManager

from .constants import (
    CONVERSATION_HISTORY_RESERVE,
    MIN_CONTEXT_BUDGET,
    MODEL_RESPONSE_RESERVE,
    SYSTEM_PROMPT_RESERVE,
)
from .exceptions import ResourceUnavailableError
from .models import ResourceState


class ResourceManager:
    """Maintain runtime resource state."""

    def __init__(
        self,
        provider_manager: ProviderManager,
    ) -> None:
        self._provider_manager = provider_manager

    def state(self) -> ResourceState:
        """Return the current model state."""

        if not self._provider_manager.health_check():
            raise ResourceUnavailableError(
                "Provider is offline."
            )

        model: ModelInfo = self._provider_manager.model_info()

        return ResourceState(
            provider=self._provider_manager.provider_info().name,
            model=model.name,
            context_window=model.context_window,
            quantization=model.quantization,
            estimated_ram_mb=model.estimated_ram_mb,
            supports_streaming=model.supports_streaming,
            supports_tools=model.supports_tools,
            supports_grammar=model.supports_grammar,
        )

    def validate(self) -> ResourceState:
        """Validate runtime resources."""

        state = self.state()

        if not state.model:
            raise ResourceUnavailableError(
                "No model is loaded."
            )

        return state

    def context_budget(self) -> int:
        """Return the usable context window."""

        state = self.state()

        budget = (
            state.context_window
            - SYSTEM_PROMPT_RESERVE
            - CONVERSATION_HISTORY_RESERVE
            - MODEL_RESPONSE_RESERVE
        )

        return max(
            budget,
            MIN_CONTEXT_BUDGET,
        )