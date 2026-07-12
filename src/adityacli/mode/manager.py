from __future__ import annotations

from .models import Mode

class ModeManager:
    """Manage the active execution mode."""

    def __init__(self) -> None:
        self._mode: Mode | None = None

    @property
    def mode(self) -> Mode | None:
        """Return the active execution mdoe."""

        return self._mode
    
    def set_mode(self, name: str) -> None:
        """Set the active execution mode."""

        self._mode = Mode(name=name)

    @property
    def active(self) -> bool:
        """Return whether an execution mode is active."""

        return self._mode is not None
    
    def clear(self) -> None:
        """Clear the active execution mode."""

        self._mode = None