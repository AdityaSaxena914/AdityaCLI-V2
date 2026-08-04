from __future__ import annotations

import hashlib
from adityacli.config import AppConfig
from adityacli.constants import DEFAULT_ENCODING, FILE_HEADER
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


class EditTool(BaseTool):
    """Generate a complete replacement for an existing file."""
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._token_counter = CharacterTokenCounter()
        self._max_tokens = (
            self._config.workspace.max_file_size
            // CharacterTokenCounter.CHARS_PER_TOKEN
        )

    def execute(self, command: Command) -> ToolResult:
        if len(command.arguments) != 1:
            raise InvalidPathError(
                "Expected exactly one file path."
            )

        workspace = self._config.workspace.root.resolve()
        relative_path = command.arguments[0]

        path = (workspace / relative_path).resolve()

        if not path.is_relative_to(workspace):
            raise InvalidPathError(
                "Path is outside the workspace."
            )

        if not path.exists():
            raise FileNotFoundError(relative_path)

        if not path.is_file():
            raise InvalidPathError(
                f"{relative_path} is not a file."
            )

        content = path.read_text(
            encoding=DEFAULT_ENCODING,
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