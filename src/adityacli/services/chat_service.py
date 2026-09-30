from __future__ import annotations

from dataclasses import dataclass, replace

from adityacli.core.models import (
    ChatResponse,
    Command,
    LLMResponse,
    OverwriteRequest,
    PendingSelectionRequest,
    RuntimeResult,
    ToolResult,
)
from adityacli.core.session import Session
from adityacli.exceptions import AmbiguousPathError
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService


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
    ) -> None:
        self._commands: CommandService = command_service
        self._llm: LLMService = llm_service
        self._overwrite: OverwriteService = overwrite_service

    def chat(
        self,
        *,
        session: Session,
        text: str,
    ) -> ChatServiceResult:
        command = self._commands.parse(text)

        if command is None:
            session.add_user(text)
            return self._generate(
                session=session,
                command=None,
                tool_result=None,
            )

        try:
            tool_result = self._commands.execute(command)
        except AmbiguousPathError as exc:
            return ChatServiceResult(
                result=PendingSelectionRequest(
                    query=exc.query,
                    candidates=tuple(exc.candidates),
                    original_command=command,
                ),
                llm_response=None,
            )

        return self._run_tool_result(
            session=session,
            command=command,
            tool_result=tool_result,
            text=text,
        )

    def resolve_selection(
        self,
        *,
        session: Session,
        request: PendingSelectionRequest,
        index: int,
    ) -> ChatServiceResult:
        """
        Re-run a /read whose argument was disambiguated by the user.
        The CLI only supplies the chosen index; resolution stays here.
        """

        selected_path = request.candidates[index]

        resolved_command: Command = replace(
            request.original_command,
            arguments=[selected_path],
        )

        tool_result = self._commands.execute(resolved_command)

        return self._run_tool_result(
            session=session,
            command=resolved_command,
            tool_result=tool_result,
            text=f"/read {{{selected_path}}}",
        )

    def _run_tool_result(
        self,
        *,
        session: Session,
        command: Command,
        tool_result: ToolResult,
        text: str,
    ) -> ChatServiceResult:
        session.add_user(text)

        for path, content in tool_result.metadata.files_read:
            session.remember_file(path, content)

        if not tool_result.requires_llm:
            # Deterministic display output (plain /read, /search, /git)
            # is shown to the user, but the raw dump never enters the
            # persisted transcript (chat.jsonl) -- that would silently
            # refill the context window on every later turn. Read
            # files are still available to follow-up questions via
            # session.read_files, a separately bounded cache injected
            # fresh into each LLM call (see PromptBuilder.build).
            return ChatServiceResult(
                result=ChatResponse(tool_result.prompt),
                llm_response=None,
            )

        return self._generate(
            session=session,
            command=command,
            tool_result=tool_result,
        )

    def _generate(
        self,
        *,
        session: Session,
        command: Command | None,
        tool_result: ToolResult | None,
    ) -> ChatServiceResult:
        llm_response = self._llm.generate(
            session=session,
            tool_result=tool_result,
        )

        response = llm_response.content

        if command is not None:
            request = self._overwrite.create_request(command, response)

            if request is not None:
                return ChatServiceResult(
                    result=request,
                    llm_response=llm_response,
                )

        return ChatServiceResult(
            result=ChatResponse(response),
            llm_response=llm_response,
        )

    def confirm_overwrite(self, request: OverwriteRequest) -> None:
        self._overwrite.confirm(request)

    def needs_followup(self, text: str) -> str | None:
        return self._commands.needs_followup(text)

    def confirmation_message(
        self,
        request: OverwriteRequest,
        command_text: str,
    ) -> str:
        return self._overwrite.confirmation_message(request, command_text)
