from __future__ import annotations

import shutil
from pathlib import Path

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


class MoveFileTool(ToolInterface):

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="move_file",
            description="Move a file.",
            category=ToolCategory.FILESYSTEM,
            permission=PermissionType.WRITE,
            parameters=[
                ToolParameter(
                    name="source",
                    type="string",
                    description="Source file.",
                    required=True,
                ),
                ToolParameter(
                    name="destination",
                    type="string",
                    description="Destination file.",
                    required=True,
                ),
            ],
        )

    def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        src = request.arguments.get("source")
        dst = request.arguments.get("destination")

        if not isinstance(src, str):
            raise ToolValidationError("Argument 'source' is required.")

        if not isinstance(dst, str):
            raise ToolValidationError("Argument 'destination' is required.")

        workspace = request.context.workspace_manager

        try:
            source = workspace.resolve(Path(src))
            destination = workspace.resolve(Path(dst))

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.move(
                str(source),
                str(destination),
            )

            return ToolExecutionResult(
                success=True,
                content=f"Moved '{src}' -> '{dst}'.",
            )

        except OSError as exc:
            raise ToolExecutionError(str(exc)) from exc