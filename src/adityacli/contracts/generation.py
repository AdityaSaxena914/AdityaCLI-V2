from pydantic import BaseModel, Field
from .chat import ChatMessage
from .tools import ToolDefinition

class GenerationConfig(BaseModel):
    """Generation parameters."""

    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


class GenerationRequest(BaseModel):
    """A request sent to a provider."""

    messages: list[ChatMessage]
    tools: list[ToolDefinition] = Field(default_factory=list)
    config: GenerationConfig


class GenerationResponse(BaseModel):
    """A response returned by a provider."""

    message: ChatMessage
    model: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None