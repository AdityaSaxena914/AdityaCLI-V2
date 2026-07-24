from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adityacli.workspace.manager import WorkspaceManager
    from adityacli.security.manager import SecurityManager


@dataclass(slots=True)
class ToolExecutionContext:
    workspace_manager: "WorkspaceManager"
    security_manager: "SecurityManager"