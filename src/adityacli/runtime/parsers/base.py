from __future__ import annotations

from abc import ABC, abstractmethod

from ..parser_models import RuntimePlan


class Parser(ABC):
    @abstractmethod
    def parse(self, prompt: str) -> RuntimePlan:
        ...