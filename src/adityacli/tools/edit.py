from __future__ import annotations
from typing import override
import hashlib
from adityacli.config import AppConfig
from adityacli.constants import FILE_HEADER
from adityacli.core.models import (
    CachedFile,
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.exceptions import (
    FileTooLargeError,
    InvalidPathError,
)
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.core.workspace_guard import WorkspaceGuard


class EditTool(BaseTool):
    """Generate a complete replacement for an existing file."""
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._guard: WorkspaceGuard = WorkspaceGuard(config)
        self._token_counter: CharacterTokenCounter = CharacterTokenCounter()
        self._max_tokens: int = (
            self._config.workspace.max_file_size
            // CharacterTokenCounter.CHARS_PER_TOKEN
        )

    @override
    def execute(self, command: Command) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidPathError(
                "Expected exactly one file path."
            )

        relative_path = command.arguments[0]

        path = self._guard.existing_file(
            relative_path
        )

        content = path.read_text(
            encoding=self._config.workspace.encoding,
        )

        estimated_tokens = self._token_counter.count_text(content)

        if estimated_tokens > self._max_tokens:
            raise FileTooLargeError(
                f"{relative_path} exceeds the maximum token limit."
            )

        prompt = (
            load_prompt("edit")
            + "\n\n"
            + FILE_HEADER.format(path=relative_path)
            + "\n"
            + content
            + "\n\n=== USER REQUEST ===\n"
            + command.prompt
        )

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                files_read=(
                    CachedFile(
                        path=relative_path,
                        content=content,
                        sha256=hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest(),
                    ),
                ),
                files_written=(relative_path,),
            ),
        )