from __future__ import annotations

from pydantic import BaseModel, Field


class RuntimeStep(BaseModel):
    tool: str
    arguments: dict[str, object] = Field(default_factory=dict)


class RuntimePlan(BaseModel):
    steps: list[RuntimeStep] = Field(default_factory=list)

    @property
    def empty(self) -> bool:
        return len(self.steps) == 0