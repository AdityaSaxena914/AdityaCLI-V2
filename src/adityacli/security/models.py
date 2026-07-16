from __future__ import annotations

from pydantic import BaseModel

class Permission(BaseModel):
    """Represents a tool permission."""

    category: str

class Policy(BaseModel):
    """Represents a security policy."""

    name: str

class SecurityDecision(BaseModel):
    """Represents the result of a security validation."""

    allowed: bool
    reason: str | None = None