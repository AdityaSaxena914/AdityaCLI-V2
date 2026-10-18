from __future__ import annotations
from typing import override
import os
from contextlib import closing
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
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.core.operations import check_operation, bounded_tool
from adityacli.core.processes import ProcessOutput, capture_process


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

    _PATH_COMMANDS: set[str] = {
        "add",
        "restore",
    }

    _FORBIDDEN_PREFIXES: tuple[str, ...] = (
        "-c",
        "--config",
        "--config-env",
        "--exec-path",
        "--upload-pack",
        "--receive-pack",
        "--template",
    )

    _FORBIDDEN_SUBSTRINGS: tuple[str, ...] = (
        "ext::",
        "fd::",
    )

    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._workspace: Path = config.workspace.root.resolve()
        self._guard = WorkspaceGuard(config)

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

        paths_only = False
        for arg in arguments[1:]:
            if skip_next:
                skip_next = False
                continue
            if arg == "--":
                paths_only = True
                continue

            if paths_only:
                self._validate_path(arg)
                continue

            for forbidden in self._FORBIDDEN_PREFIXES:
                if (arg == forbidden and arg not in allowed_flags) or arg.startswith(f"{forbidden}="):
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

            if subcommand in self._PATH_COMMANDS or Path(arg).is_absolute() or Path(arg).drive or ".." in Path(arg).parts:
                self._validate_path(arg)

        if skip_next:
            raise ValidationError("Missing value for a Git option.")

    def _isolated_repository(self) -> dict[str, str]:
        git_dir = self._guard.resolve(".git")
        if not git_dir.is_dir():
            raise InvalidPathError("Git requires a repository rooted in the working directory. Linked worktrees are not supported.")
        # Git can traverse its own metadata independently of Python. Check
        # that tree too, including objects shared through hard links.
        for directory, directories, files in os.walk(git_dir, followlinks=False):
            check_operation()
            for name in [*directories, *files]:
                self._guard.resolve(str((Path(directory) / name).relative_to(self._workspace)))
        for name in ("commondir", "objects/info/alternates"):
            if self._guard.resolve(f".git/{name}").exists():
                raise InvalidPathError("Git metadata must be contained in the working directory.")
        environment = self._environment()
        for config_name in ("config", "config.worktree"):
            config_path = self._guard.resolve(f".git/{config_name}")
            if not config_path.exists():
                continue
            # Git's grammar includes tabs, quoted subsections, and deprecated
            # dotted sections. Parse canonical keys with Git, never ConfigParser.
            status, data, truncated = capture_process(
                ["git", "--no-pager", "config", "--no-includes", "--null",
                 "--file", str(config_path), "--list"], cwd=self._workspace,
                env=environment, timeout=self._config.execution.tool_timeout,
                max_bytes=self._config.workspace.max_file_size,
            )
            if status or truncated:
                raise ValidationError("Cannot safely parse repository configuration.")
            for record in data.decode("utf-8", errors="strict").split("\0"):
                if not record:
                    continue
                key, _, value = record.partition("\n")
                lowered = key.lower()
                category = lowered.split(".", 1)[0]
                if category in {"include", "includeif", "filter"} or (category == "merge" and lowered.count(".") > 1):
                    raise ValidationError("Git includes, filters and custom merge drivers are disabled in workspace mode.")
                if lowered.rsplit(".", 1)[-1] in {"sslcainfo", "sslcapath", "sslcert", "sslkey"} and value:
                    self._guard.resolve(value)
        todo = self._guard.resolve(".git/rebase-merge/git-rebase-todo")
        if todo.exists():
            with todo.open(encoding="utf-8") as file:
                if any(line.lstrip().startswith(("exec ", "x ")) for line in file):
                    raise ValidationError("Rebase execution steps are disabled in workspace mode.")
        self._guard.resolve(".gitignore")
        return environment

    @staticmethod
    def _environment() -> dict[str, str]:
        # Exclude inherited paths/config and global config, which may read
        # project data or invoke helpers outside this workspace.
        identity = {"GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"}
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_") or key in identity}
        environment.update({
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull, "GIT_ATTR_NOSYSTEM": "1",
            "GIT_ALLOW_PROTOCOL": "http:https", "GIT_TERMINAL_PROMPT": "0",
            "GIT_EDITOR": "true", "GIT_SEQUENCE_EDITOR": "true",
        })
        return environment

    def _check_worktree_paths(self, prefix: list[str], environment: dict[str, str]) -> None:
        """Use Git's ignore rules to avoid scanning ignored dependencies."""
        process = ProcessOutput([*prefix, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                                cwd=self._workspace, env=environment,
                                timeout=self._config.execution.tool_timeout)
        with closing(iter(process)) as chunks:
            pending = b""
            for chunk in chunks:
                pending += chunk
                paths = pending.split(b"\x00")
                pending = paths.pop()
                if len(pending) > 65536:
                    raise ToolExecutionError("Git returned an oversized path.")
                for path in paths:
                    self._guard.resolve(path.decode("utf-8"))
            if process.returncode or pending:
                raise ToolExecutionError("Git could not validate working-directory paths.")

    @override
    @bounded_tool
    def execute(
        self,
        command: Command,
    ) -> ToolResult:
        self._validate(command.arguments)
        environment = self._isolated_repository()
        arguments = list(command.arguments)
        if arguments[0] == "log" and "-n" not in arguments:
            arguments[1:1] = ["-n", "50"]
        if arguments[0] in {"diff", "show", "log"}:
            arguments[1:1] = ["--no-ext-diff", "--no-textconv"]
        git_command = [
            "git", "--no-pager", f"--git-dir={self._workspace / '.git'}", f"--work-tree={self._workspace}",
            "-c", f"core.hooksPath={self._workspace / '.git' / 'HEAD'}",
            "-c", "core.fsmonitor=false", "-c", "credential.helper=",
            "-c", "commit.gpgSign=false", "-c", "tag.gpgSign=false",
            "-c", f"core.excludesFile={self._workspace / '.git' / 'adityacli-unused'}",
            "-c", f"core.attributesFile={self._workspace / '.git' / 'adityacli-unused'}",
        ]

        try:
            self._check_worktree_paths(git_command, environment)
            git_command.extend(arguments)
            return_code, data, truncated = capture_process(
                git_command, cwd=self._workspace, env=environment,
                timeout=self._config.execution.tool_timeout,
            )
            output = data.decode("utf-8", errors="replace").strip()
            if truncated:
                output += "\n... output truncated at 128 KiB."
        except OSError as exc:
            raise ToolExecutionError(
                f"Failed to execute git: {exc}"
            ) from exc

        if not output:
            output = "Git command produced no output."

        if return_code:
            raise ToolExecutionError(f"Git exited with code {return_code}:\n{output}")

        prompt = (
            f"Git command:\n"
            f"git {' '.join(command.arguments)}\n\n"
            f"Output:\n{output}"
        )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                git_command="git " + " ".join(command.arguments),
                extra={
                    "return_code": return_code,
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

        self._guard.resolve(relative_path)
