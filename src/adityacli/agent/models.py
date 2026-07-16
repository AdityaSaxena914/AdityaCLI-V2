from __future__ import annotations

from pydantic import BaseModel

class Agent(BaseModel):
    """Represents an agent."""

    name: str

class AgentInfo(BaseModel):
    """Metadata about an agent."""

    name: str
    description: str

class AgentRequest(BaseModel):
    """Agent execution request."""

    prompt: str

class AgentResponse(BaseModel):
    """Agent execution response."""

    response: str