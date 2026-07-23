from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    Permission,
    Policy,
    SecurityDecision,
)

class SecurityPolicy(ABC):
    """Contract implemented by every security policy."""

    @abstractmethod
    def policy(self) -> Policy:
        """Return the policy metadata."""
        ...
        
        
    @abstractmethod
    def validate(
        self,
        permission: Permission,
    ) -> SecurityDecision:
        """Validate a permission request."""
        ...