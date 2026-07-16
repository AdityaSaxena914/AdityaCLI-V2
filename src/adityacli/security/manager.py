from __future__ import annotations

from .models import (
    Permission,
    SecurityDecision,
)
from .validators import SecurityValidator

class SecurityManager:
    """Manage runtime security validation."""

    def validate(
        self,
        permission: Permission,
    ) -> SecurityDecision:
        """Validate a permission request."""

        return SecurityValidator.validate(permission)