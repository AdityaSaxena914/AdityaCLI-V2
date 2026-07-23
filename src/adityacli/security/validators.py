from __future__ import annotations

from .models import (
    Permission,
    SecurityDecision,
    SecurityOutcome,
)

class SecurityValidator:
    """Validate security requests."""

    @staticmethod
    def validate(
        permission: Permission,
    ) -> SecurityDecision:
        """Validate a permission request."""

        return SecurityDecision(
            outcome=SecurityOutcome.ALLOW,
            requires_confirmation=True,
        )