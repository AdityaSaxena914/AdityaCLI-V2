import subprocess

from config import AppConfig
from core.models import Command
from exceptions import GitError, InvalidSyntaxError
from tools.base import BaseTool


class GitTool(BaseTool):
    """Git tool."""

    @property
    def name(self) -> str:
        return "git"

    def execute(self, command: Command) -> str:
        if not command.arguments:
            raise InvalidSyntaxError("Git subcommand is required.")

        result = subprocess.run(
            ["git", *command.arguments],
            cwd=self._config.workspace.root,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise GitError(result.stderr.strip() or "Git command failed.")

        output = result.stdout.strip()

        return (
            f"Git Command:\n"
            f"git {' '.join(command.arguments)}\n\n"
            f"Git Output:\n"
            f"{output}\n\n"
            f"User Request:\n"
            f"{command.prompt}"
        )