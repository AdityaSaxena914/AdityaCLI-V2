from __future__ import annotations

from pathlib import Path

from adityacli.contracts.tools import (
    PermissionType,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter,
)
from adityacli.tool.exceptions import ToolValidationError

from ..interface import ToolInterface


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".mypy_cache",
    ".idea",
    ".vscode",
}


class WorkspaceSearchTool(ToolInterface):
    """Search for files inside the active workspace."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_search",
            description="Search for files by name inside the workspace.",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Filename or partial filename.",
                    required=True,
                )
            ],
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.READ,
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        query = request.arguments.get("query")

        if not isinstance(query, str) or not query.strip():
            raise ToolValidationError(
                "Argument 'query' is required."
            )

        workspace = request.context.workspace_manager.workspace.root

        matches: list[str] = []

        for path in workspace.rglob("*"):

            if not path.is_file():
                continue

            if any(
                part in IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            if query.lower() in path.name.lower():
                matches.append(
                    str(path.relative_to(workspace))
                )

        matches.sort()

        return ToolExecutionResult(
            success=True,
            content="\n".join(matches)
            if matches
            else "No matching files found.",
            metadata={
                "count": len(matches),
            },
        )