from __future__ import annotations

import subprocess
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import ToolExecutionError
from adityacli.tools.base import BaseTool


class GitTool(BaseTool):
    """Execute deterministic Git commands."""
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def execute(self, command: Command) -> ToolResult:
        if not command.arguments:
            raise ToolExecutionError(
                "Git command cannot be empty."
            )

        git_command = ["git", *command.arguments]

        try:
            result = subprocess.run(
                git_command,
                cwd=self._config.workspace.root,
                capture_output=True,
                text=True,
                shell=False,
                check=False,
            )
        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to execute git: {exc}"
            ) from exc

        output = result.stdout.strip()

        if result.stderr.strip():
            if output:
                output += "\n\n"
            output += result.stderr.strip()

        if not output:
            output = "Git command produced no output."

        prompt = (
            f"Git command:\n"
            f"{' '.join(git_command)}\n\n"
            f"Output:\n{output}"
        )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                git_command=" ".join(git_command),
                extra={
                    "return_code": result.returncode,
                },
            ),
            requires_llm=False,
        )