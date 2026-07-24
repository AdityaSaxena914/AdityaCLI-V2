from __future__ import annotations
from .exceptions import SessionNotActiveError
from .models import Session

class SessionManager:
    """Manage the active application session."""
    
    def __init__(self) -> None:
        self._session: Session | None = None

    @property
    def session(self) -> Session:
        """Return the active session."""

        if self._session is None:
            raise SessionNotActiveError(
                "No active session."
            )

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