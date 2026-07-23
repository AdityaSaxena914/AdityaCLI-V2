from __future__ import annotations

from adityacli.contracts.provider import ModelInfo
from adityacli.provider import ProviderManager

from .exceptions import ResourceUnavailableError
from .models import ResourceState

from .constants import (
    CONVERSATION_HISTORY_RESERVE,
    MIN_CONTEXT_BUDGET,
    MODEL_RESPONSE_RESERVE,
    SYSTEM_PROMPT_RESERVE,
)


class ResourceManager:
    """Manage runtime resources."""

    def __init__(
        self,
        provider_manager: ProviderManager,
    ) -> None:
        self._provider_manager = provider_manager

    def state(self) -> ResourceState:
        """Return the current runtime resource state."""

        if not self._provider_manager.health_check():
            return ResourceState(
                provider_online=False,
                model_loaded=False,
            )

        model: ModelInfo = self._provider_manager.model_info()

        return ResourceState(
            provider_online=True,
            model_loaded=True,
            model_name=model.name,
            context_window=model.context_window,
            quantization=model.quantization,
            estimated_ram_mb=model.estimated_ram_mb,
        )

    def validate(self) -> None:
        """Ensure resources are available."""

        state = self.state()

        if not state.provider_online:
            raise ResourceUnavailableError(
                message="Provider is offline."
            )

        if not state.model_loaded:
            raise ResourceUnavailableError(
                message="No model is loaded."
            )

    def context_budget(self) -> int:
        """Return the available context budget."""

        model = self._provider_manager.model_info()

        reserved_response = 12000
        reserved_system = 2000
        reserved_history = 8000

        budget = (
            model.context_window
            - SYSTEM_PROMPT_RESERVE
            - CONVERSATION_HISTORY_RESERVE
            - MODEL_RESPONSE_RESERVE
        )

        return max(
            budget,
            MIN_CONTEXT_BUDGET,
        )