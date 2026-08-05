from __future__ import annotations

from adityacli.core.file_manager import FileManager
from adityacli.core.models import (
    Command,
    OverwriteRequest,
    Tool,
)
from adityacli.core.response_parser import ResponseParser
from adityacli.core.session_store import SessionStore


class OverwriteService:
    """
    Handle write/edit response parsing and file persistence.
    """

    def __init__(
        self,
        parser: ResponseParser,
        file_manager: FileManager,
        store: SessionStore,
    ) -> None:
        self._parser = parser
        self._file_manager = file_manager
        self._store = store

    def create_request(
        self,
        command: Command,
        response: str,
    ) -> OverwriteRequest | None:
        if command.tool is Tool.WRITE:
            files = self._parser.parse_write_response(
                response=response,
                paths=command.arguments,
            )
            return OverwriteRequest(files)

        if command.tool is Tool.EDIT:
            content = self._parser.parse_edit_response(
                response,
            )

            return OverwriteRequest(
                {
                    command.arguments[0]: content,
                }
            )

        return None

    def confirm(
        self,
        request: OverwriteRequest,
    ) -> None:
        self._file_manager.write_many(
            request.files,
            overwrite=True,
        )

        for path, content in request.files.items():
            self._store.cache_file(
                path=path,
                content=content,
            )

        self._store.flush_memory()