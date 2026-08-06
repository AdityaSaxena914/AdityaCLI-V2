from __future__ import annotations
from collections.abc import Iterator
from adityacli.core.models import (
    ChatResponse,
    RuntimeResult,
    LLMResponse,
    OverwriteRequest,
)
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService
from dataclasses import dataclass


@dataclass(slots=True)
class ChatServiceResult:
    result: RuntimeResult
    llm_response: LLMResponse | None


class ChatService:
    """Coordinates one complete chat interaction."""

    def __init__(
        self,
        command_service: CommandService,
        llm_service: LLMService,
        overwrite_service: OverwriteService,
        store: SessionStore,
    ) -> None:
        self._commands: CommandService = command_service
        self._llm: LLMService = llm_service
        self._overwrite: OverwriteService = overwrite_service
        self._store: SessionStore = store

    def chat(
        self,
        *,
        session: Session,
        text: str,
    ) -> ChatServiceResult:
        command = self._commands.parse(text)

        tool_result = None

        if command is None:
            session.add_user(text)
        else:
            tool_result = self._commands.execute(command)

            if not tool_result.requires_llm:
                session.add_user(text)
                session.add_assistant(tool_result.prompt)

                self._store.flush_memory()

                return ChatServiceResult(
                    result=ChatResponse(tool_result.prompt),
                    llm_response=None,
                )

            for cached_file in tool_result.metadata.files_read:
                self._store.cache_file(
                    path=cached_file.path,
                    content=cached_file.content,
                )

            session.add_user(text)

        llm_response = self._llm.generate(
            session=session,
            tool_result=tool_result,
        )

        response = llm_response.content

        if command is None:
            self._store.flush_memory()

            return ChatServiceResult(
                result=ChatResponse(response),
                llm_response=llm_response,
            )

        request = self._overwrite.create_request(
            command,
            response,
        )

        if request is not None:
            self._store.flush_memory()

            return ChatServiceResult(
                result=request,
                llm_response=llm_response,
            )

        self._store.flush_memory()

        return ChatServiceResult(
            result=ChatResponse(response),
            llm_response=llm_response,
        )


    def chat_stream(
        self,
        *,
        session: Session,
        text: str,
    ) -> Iterator[str]:
        command = self._commands.parse(text)

        tool_result = None

        if command is None:
            session.add_user(text)
        else:
            tool_result = self._commands.execute(command)

            if not tool_result.requires_llm:
                session.add_user(text)
                session.add_assistant(tool_result.prompt)

                self._store.flush_memory()

                yield tool_result.prompt
                return

            for cached_file in tool_result.metadata.files_read:
                self._store.cache_file(
                    path=cached_file.path,
                    content=cached_file.content,
                )

            session.add_user(text)

        chunks: list[str] = []

        for chunk in self._llm.stream(
            session=session,
            tool_result=tool_result,
        ):
            chunks.append(chunk)
            yield chunk

        session.add_assistant("".join(chunks))

        self._store.flush_memory()


    def confirm_overwrite(
        self,
        request: OverwriteRequest,
    ) -> None:
        self._overwrite.confirm(request)

    def needs_followup(
        self,
        text: str,
    ) -> str | None:
        return self._commands.needs_followup(text)

    def confirmation_message(
        self,
        request: OverwriteRequest,
        command_text: str,
    ) -> str:
        return self._overwrite.confirmation_message(
            request,
            command_text,
        )

    
    @property
    def last_response(self) -> LLMResponse | None:
        return self._llm.last_response