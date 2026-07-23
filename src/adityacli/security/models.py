from __future__ import annotations
from enum import Enum
from pydantic import BaseModel
from adityacli.contracts.tools import PermissionType




class SecurityOutcome(str, Enum):
    """Possible security decisions."""

    ALLOW = "allow"
    REJECT = "reject"
    SANDBOX = "sandbox"


class Permission(BaseModel):
    """Permission requested by a tool."""

    permission: PermissionType


class Policy(BaseModel):
    """Security policy metadata."""

    name: str


class SecurityDecision(BaseModel):
    """Result returned by the Security subsystem."""

    outcome: SecurityOutcome

    reason: str | None = None

    requires_confirmation: bool = False