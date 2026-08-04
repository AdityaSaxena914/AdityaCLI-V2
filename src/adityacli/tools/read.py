from __future__ import annotations

import hashlib
from adityacli.config import AppConfig
from adityacli.core.models import (
    CachedFile,
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.exceptions import FileTooLargeError
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt


class ReadTool(BaseTool):
    """
    Read one or more files from the workspace.

    The Runtime decides whether these files should be persisted into
    session memory.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._workspace = config.workspace.root.resolve()
        self._token_counter = CharacterTokenCounter()
        self._max_tokens = (
            self._config.workspace.max_file_size
            // CharacterTokenCounter.CHARS_PER_TOKEN
        )

    def execute(self, command: Command) -> ToolResult:
        sections: list[str] = []
        files_read: list[CachedFile] = []

        for relative_path in command.arguments:
            path = self._workspace / relative_path

            content = path.read_text(encoding="utf-8")
            estimated_tokens = self._token_counter.count_text(content)

            if estimated_tokens > self._max_tokens:
                raise FileTooLargeError(
                    f"{relative_path} exceeds the maximum token limit."
                )

            files_read.append(
                CachedFile(
                    path=relative_path,
                    content=content,
                    sha256=self._sha256(content),
                )
            )

            sections.append(
                "\n".join(
                    [
                        "===== BEGIN UNTRUSTED FILE =====",
                        f"=== FILE: {relative_path} ===",
                        content,
                        "===== END UNTRUSTED FILE =====",
                        "",
                    ]
                )
            )


        prompt = (
            load_prompt("read")
            + "\n\n"
            + "\n".join(sections)
        )
        
        if command.prompt:
            prompt += (
                "\n=== USER REQUEST ===\n"
                + command.prompt
            )
        else:
            prompt += (
                "\n=== USER REQUEST ===\n"
                "Read and understand these files."
            )            

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                files_read=tuple(files_read),
            ),
        )

    @staticmethod
    def _sha256(content: str) -> str:
        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()