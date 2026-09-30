from __future__ import annotations
from typing import override
from pathlib import Path
from adityacli.config import AppConfig
from adityacli.core.models import (
    Command,
    ToolMetadata,
    ToolResult,
)
from adityacli.core.token_counter import CharacterTokenCounter
from adityacli.core.path_resolver import PathResolver
from adityacli.exceptions import AmbiguousPathError, FileTooLargeError
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.tools.base import BaseTool
from adityacli.prompts import load_prompt


class ReadTool(BaseTool):
    """
    Read one or more files from the workspace.

    Resolution order per argument:
      1. Exact workspace-relative path (fast path, unchanged behavior
         for already-correct paths).
      2. Fall back to PathResolver.find_by_name -- the same resolver
         /search uses. Exactly one match -> proceed. Zero matches ->
         FileNotFoundError. More than one -> AmbiguousPathError,
         caught upstream (ChatService) and turned into a
         PendingSelectionRequest; this tool never talks to the CLI.

    When no natural-language prompt is attached, this is a pure
    display command (requires_llm=False) -- file content streams to
    the terminal directly, no LLM round-trip. A prompt attached to
    /read ("summarize this") is the one case that still needs the LLM.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._guard: WorkspaceGuard = WorkspaceGuard(config)
        self._resolver: PathResolver = PathResolver(config)
        self._token_counter: CharacterTokenCounter = CharacterTokenCounter()

        self._max_tokens: int = (
            config.workspace.max_file_size
            // CharacterTokenCounter.CHARS_PER_TOKEN
        )

    def _resolve_one(self, query: str) -> Path:
        try:
            return self._guard.existing_file(query)
        except (FileNotFoundError, OSError):
            pass

        matches = self._resolver.find_by_name(query)

        if not matches:
            raise FileNotFoundError(query)

        if len(matches) > 1:
            workspace = self._resolver.workspace
            raise AmbiguousPathError(
                query=query,
                candidates=[
                    str(path.relative_to(workspace))
                    for path in matches
                ],
            )

        return matches[0]

    @override
    def execute(self, command: Command) -> ToolResult:
        workspace = self._resolver.workspace
        display_sections: list[str] = []
        llm_sections: list[str] = []
        files_read: list[tuple[str, str]] = []

        for query in command.arguments:
            path = self._resolve_one(query)
            relative_path = str(path.relative_to(workspace))

            content = path.read_text(
                encoding=self._config.workspace.encoding,
            )
            estimated_tokens = self._token_counter.count_text(content)

            if estimated_tokens > self._max_tokens:
                raise FileTooLargeError(
                    f"{relative_path} exceeds the maximum token limit."
                )

            files_read.append((relative_path, content))

            display_sections.append(
                "\n".join(
                    [
                        f"=== FILE: {relative_path} ===",
                        content,
                        "",
                    ]
                )
            )

            llm_sections.append(
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

        if command.prompt:
            prompt = (
                load_prompt("read")
                + "\n\n"
                + "\n".join(llm_sections)
                + "\n=== USER REQUEST ===\n"
                + command.prompt
            )
            requires_llm = True
        else:
            prompt = "\n".join(display_sections)
            requires_llm = False

        return ToolResult(
            prompt=prompt,
            metadata=ToolMetadata(
                files_read=tuple(files_read),
            ),
            requires_llm=requires_llm,
        )
