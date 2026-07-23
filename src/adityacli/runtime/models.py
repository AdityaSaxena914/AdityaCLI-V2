from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class PipelineType(str, Enum):
    """Execution pipelines."""

    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"
    REASONING = "reasoning"
    AMBIGUOUS = "ambiguous"


class RuntimeRequest(BaseModel):
    """Incoming runtime request."""

    prompt: str


class RuntimeContext(BaseModel):
    """Context produced by the runtime."""

    prompt: str

    pipeline: PipelineType

    context: str | None = None

    context_budget: int


class RuntimeResponse(BaseModel):
    """Final runtime response."""

    content: str


class IntentResult(BaseModel):
    """Result produced by the Intent Router."""

    pipeline: PipelineType

    confidence: float

    tool: str | None = None


class ResourceState(BaseModel):
    """Current runtime resource state."""

    provider_online: bool

    model_loaded: bool

    model_name: str | None = None

    context_window: int | None = None

    quantization: str | None = None

    estimated_ram_mb: int | None = None


class PromptContext(BaseModel):
    """Prompt sent to the provider."""

    system_prompt: str

    user_prompt: str


class GrammarContext(BaseModel):
    """Grammar configuration."""

    enabled: bool = False

    grammar: str | None = None