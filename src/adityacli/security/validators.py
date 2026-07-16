from __future__ import annotations

from .models import (
    Permission,
    SecurityDecision,
)

class SecurityValidator:
    """Validate security requests."""

    @staticmethod
    def validate(
        permission: Permission,
    ) -> SecurityDecision:
        """Validate a permission request."""

        return SecurityDecision(
            allowed=True,
        )