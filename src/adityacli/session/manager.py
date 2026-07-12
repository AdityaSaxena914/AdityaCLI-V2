from __future__ import annotations

from .models import Session

class SessionManager:
    """Manage the active application session."""
    
    def __init__(self) -> None:
        self._session: Session | None = None

    @property
    def session(self) -> Session | None:
        """Return the active session."""

        return self._session
    
    def create(self) -> Session:
        """Create a new session."""

        self._session = Session()

        return self._session
    
    @property
    def active(self) -> bool:
        """Return whether a session is active."""

        return self._session is not None
    
    def destroy(self) -> None:
        """Destroy the active session."""

        self._session = None