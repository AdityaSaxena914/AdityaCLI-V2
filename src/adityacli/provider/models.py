from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str
    content: str

class GenerationConfig(BaseModel):
    """Generation parameters."""

    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False

class GenerationRequest(BaseModel):
    """A request sent to a provider."""

    messages: list[ChatMessage]
    config: GenerationConfig

class GenerationResponse(BaseModel):
    """A response returned by a provider."""

    content: str

class ModelInfo(BaseModel):
    """Information about a model."""

    id: str
    name: str

class ProviderInfo(BaseModel):
    """Information about a provider."""

    name: str
    endpoint: str