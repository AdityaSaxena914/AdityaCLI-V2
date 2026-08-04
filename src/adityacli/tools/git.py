from __future__ import annotations

import subprocess
from pathlib import Path

from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import (
    InvalidPathError,
    ToolExecutionError,
    ValidationError,
)
from adityacli.tools.base import BaseTool


class GitTool(BaseTool):
    """Execute deterministic Git commands."""

    _ALLOWED_COMMANDS: dict[str, set[str]] = {
        "status": {"--short", "--porcelain", "--branch"},
        "diff": {"--cached", "--staged", "--stat", "--name-only"},
        "log": {"--oneline", "--graph", "--decorate", "-n", "--all"},
        "show": set(),
        "branch": {"-a", "-r", "-d", "-D"},
        "checkout": {"-b"},
        "switch": {"-c"},
        "add": set(),
        "restore": {"--staged"},
        "reset": {"--soft", "--mixed"},
        "commit": {"-m", "--amend"},
        "fetch": set(),
        "pull": set(),
        "push": set(),
        "merge": {"--no-ff", "--ff-only"},
        "rebase": {"--continue", "--abort", "--skip"},
    }

    _PATH_COMMANDS = {
        "add",
        "restore",
    }

    _FORBIDDEN_PREFIXES = (
        "-c",
        "--config",
        "--config-env",
        "--exec-path",
        "--upload-pack",
        "--receive-pack",
        "--template",
    )

    _FORBIDDEN_SUBSTRINGS = (
        "ext::",
        "fd::",
    )

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._workspace = config.workspace.root.resolve()

    def _validate(
        self,
        arguments: list[str],
    ) -> None:
        if not arguments:
            raise ValidationError(
                "Git command cannot be empty."
            )

        subcommand = arguments[0]

        if subcommand not in self._ALLOWED_COMMANDS:
            raise ValidationError(
                f"Unsupported git command: '{subcommand}'."
            )

        allowed_flags = self._ALLOWED_COMMANDS[subcommand]

        skip_next = False

        for arg in arguments[1:]:
            if skip_next:
                skip_next = False
                continue

            for forbidden in self._FORBIDDEN_PREFIXES:
                if arg == forbidden or arg.startswith(f"{forbidden}="):
                    raise ValidationError(
                        f"Forbidden git argument: '{arg}'."
                    )

            for forbidden in self._FORBIDDEN_SUBSTRINGS:
                if forbidden in arg:
                    raise ValidationError(
                        f"Forbidden git transport: '{arg}'."
                    )

            if arg.startswith("-"):
                if arg not in allowed_flags:
                    raise ValidationError(
                        f"Flag '{arg}' is not allowed for git {subcommand}."
                    )

                if arg in {"-m", "-n", "-b", "-c"}:
                    skip_next = True

                continue

            if subcommand in self._PATH_COMMANDS:
                self._validate_path(arg)

    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        self._validate(command.arguments)

        git_command = ["git", *command.arguments]

        try:
            result = subprocess.run(
                git_command,
                cwd=self._workspace,
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

    def _validate_path(
        self,
        relative_path: str,
    ) -> None:
        """
        Ensure git path arguments stay inside the workspace.
        """

        candidate = Path(relative_path)

        if candidate.is_absolute():
            raise InvalidPathError(
                f"Absolute paths are not allowed: {relative_path}"
            )

        path = (self._workspace / candidate).resolve()

        if not path.is_relative_to(self._workspace):
            raise InvalidPathError(
                f"Path is outside the workspace: {relative_path}"
            )