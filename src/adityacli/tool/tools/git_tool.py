from __future__ import annotations

import subprocess

from adityacli.contracts.tools import (
    PermissionType,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolParameter,
)
from adityacli.tool.exceptions import (
    ToolExecutionError,
    ToolValidationError,
)

from ..interface import ToolInterface


class GitStatusTool(ToolInterface):
    """Execute git commands inside the active workspace."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="git_status",
            description="Execute a git command.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Git command to execute.",
                    required=True,
                ),
            ],
            category=ToolCategory.GIT,
            permission=PermissionType.GIT,
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        command = request.arguments.get("command")

        if not isinstance(command, str) or not command.strip():
            raise ToolValidationError(
                "Argument 'command' is required."
            )

        command = command.strip()

        if not command.lower().startswith("git"):
            command = f"git {command}"

        workspace = request.context.workspace_manager.workspace.root

        try:
            result = subprocess.run(
                command,
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            output = result.stdout.strip()

            if result.stderr.strip():
                output += (
                    "\n" if output else ""
                ) + result.stderr.strip()

            return ToolExecutionResult(
                success=result.returncode == 0,
                content=output or "(no output)",
                metadata={
                    "return_code": result.returncode,
                },
            )

        except OSError as exc:
            raise ToolExecutionError(
                str(exc),
            ) from exc