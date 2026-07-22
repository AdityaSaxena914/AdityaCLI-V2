from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information describing a language model."""

    id: str
    name: str

    context_window: int

    quantization: str | None = None

    estimated_ram_mb: int | None = None

    supports_streaming: bool = True
    supports_tools: bool = True
    supports_grammar: bool = False


class ProviderInfo(BaseModel):
    """Information describing a provider."""

    name: str

    endpoint: str

    online: bool = True