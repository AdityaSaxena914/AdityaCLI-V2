from __future__ import annotations

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    """A single deterministic tool invocation."""

    tool: str

    arguments: dict[str, object] = Field(
        default_factory=dict,
    )


class ExecutionPlan(BaseModel):
    """Ordered execution plan."""

    steps: list[ExecutionStep] = Field(
        default_factory=list,
    )

    @property
    def empty(self) -> bool:
        return len(self.steps) == 0