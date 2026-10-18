from __future__ import annotations
from adityacli.core.file_manager import FileManager
from adityacli.core.models import (
    Command,
    OverwriteRequest,
    Tool,
    ToolResult,
)
from adityacli.core.response_parser import ResponseParser
from adityacli.exceptions import ValidationError


class OverwriteService:
    """
    Handle write/edit response parsing and file persistence.
    """

    def __init__(
        self,
        parser: ResponseParser,
        file_manager: FileManager,
    ) -> None:
        self._parser: ResponseParser = parser
        self._file_manager: FileManager = file_manager

    def create_request(
        self,
        command: Command,
        response: str,
        expected_contents: dict[str, str | None] | None = None,
    ) -> OverwriteRequest | None:
        if command.tool in {Tool.WRITE, Tool.EDIT}:
            # Before parsing or rendering a potentially large response.
            self._file_manager.validate_content(response, command.arguments[0])
        if command.tool is Tool.WRITE:
            files = self._parser.parse_write_response(
                response=response,
                paths=command.arguments,
            )
            return OverwriteRequest(files, expected_contents)

        if command.tool is Tool.EDIT:
            content = self._parser.parse_edit_response(response, command.arguments[0])

            return OverwriteRequest(
                {
                    command.arguments[0]: content,
                },
                expected_contents,
            )

        return None

    def snapshot(self, command: Command | None, tool_result: ToolResult | None) -> dict[str, str | None] | None:
        """Capture targets before inference, using the exact edit input when available."""
        if command is None or command.tool not in {Tool.WRITE, Tool.EDIT}:
            return None
        if command.tool is Tool.EDIT and tool_result is not None:
            return {command.arguments[0]: tool_result.metadata.files_read[0][1]}
        return {
            path: self._file_manager.read(path) if self._file_manager.exists(path) else None
            for path in command.arguments
        }

    def confirm(self, request: OverwriteRequest) -> None:
        self._file_manager.write_many(request.files, overwrite=True, expected_contents=request.expected_contents)

    def confirmation_message(
        self,
        request: OverwriteRequest,
        command_text: str,
    ) -> str:
        existing_files = [
            path for path in request.files if self._file_manager.exists(path)
        ]

        is_overwrite = bool(existing_files)

        if command_text.startswith("/write"):
            if is_overwrite:
                return "Overwrite existing file(s)?"
            return "Write new file(s)?"

        return "Apply these changes?"
