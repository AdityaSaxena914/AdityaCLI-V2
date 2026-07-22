from pydantic import BaseModel

class ModelInfo(BaseModel):
    """Information about a model."""

    id: str
    name: str


class ProviderInfo(BaseModel):
    """Information about a provider."""

    name: str
    endpoint: str