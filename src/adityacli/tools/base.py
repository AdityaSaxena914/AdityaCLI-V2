from abc import ABC, abstractmethod

from config import AppConfig
from core.models import Command


class BaseTool(ABC):
    """Base tool."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def execute(self, command: Command) -> str:
        """
        Execute the tool.

        Returns the prompt that should be injected into the LLM.
        """
        ...