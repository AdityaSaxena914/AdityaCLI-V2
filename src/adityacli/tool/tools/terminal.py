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


class TerminalTool(ToolInterface):
    """Run terminal commands inside the active workspace."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="terminal",
            description="Execute a terminal command.",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="Command to execute.",
                    required=True,
                ),
            ],
            category=ToolCategory.TERMINAL,
            permission=PermissionType.EXECUTE,
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