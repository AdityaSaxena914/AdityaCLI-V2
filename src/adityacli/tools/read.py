from pathlib import Path
from typing import override

from adityacli.config import AppConfig
from adityacli.core.models import Command, ToolMetadata, ToolResult
from adityacli.core.path_resolver import PathResolver
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import AmbiguousPathError
from adityacli.prompts import load_prompt
from adityacli.tools.base import BaseTool


class ReadTool(BaseTool):
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._guard = WorkspaceGuard(config)
        self._resolver = PathResolver(config)

    def _resolve_one(self, query: str) -> Path:
        try:
            return self._guard.existing_file(query)
        except FileNotFoundError:
            pass
        matches = self._resolver.find_by_name(query)
        if not matches:
            raise FileNotFoundError(query)
        if len(matches) > 1:
            raise AmbiguousPathError(query, [self._guard.relative_path(str(path.relative_to(self._guard.workspace))) for path in matches])
        # Revalidate resolved matches with the same rules as exact paths.
        return self._guard.existing_file(str(matches[0].relative_to(self._guard.workspace)))

    @override
    def execute(self, command: Command) -> ToolResult:
        files: dict[str, str] = {}
        for query in command.arguments:
            path = self._resolve_one(query)
            relative = self._guard.relative_path(str(path.relative_to(self._guard.workspace)))
            if relative not in files:
                files[relative] = self._guard.read_text(relative, self._config.workspace.encoding)
        content = "\n".join(f"=== FILE: {path} ===\n{text}\n" for path, text in files.items())
        if command.prompt:
            prompt = (
                "===== BEGIN UNTRUSTED FILE =====\n" + content
                + "\n===== END UNTRUSTED FILE =====\n=== USER REQUEST ===\n" + command.prompt
            )
        else:
            prompt = content
        return ToolResult(prompt, ToolMetadata(
            files_read=tuple(files.items()),
            extra={"instructions": load_prompt("read")} if command.prompt else {},
        ), bool(command.prompt))
