from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from adityacli.core.models import (
    ChatResponse,
    Command,
    LLMResponse,
    OverwriteRequest,
    PendingSelectionRequest,
    RuntimeResult,
    ToolResult,
    Tool,
)
from adityacli.core.session import Session
from adityacli.exceptions import AmbiguousPathError, ValidationError
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
        on_chunk: Callable[[str], None] | None = None,
    ) -> ChatServiceResult:
        command = self._commands.parse(text)

        if command is not None and command.tool is Tool.REMEMBER:
            messages, files = session.restore_memory()
            return ChatServiceResult(
                ChatResponse(f"Restored {messages} messages and {files} files from memory.jsonl. "
                             "They will be included with your next request."), None,
            )

        if command is None:
            session.add_user(text)
            return self._generate(
                session=session,
                command=None,
                tool_result=None,
                on_chunk=on_chunk,
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
            on_chunk=on_chunk,
        )

    def resolve_selection(
        self,
        *,
        session: Session,
        request: PendingSelectionRequest,
        index: int,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ChatServiceResult:
        """
        Re-run a /read whose argument was disambiguated by the user.
        The CLI only supplies the chosen index; resolution stays here.
        """

        if index < 0 or index >= len(request.candidates):
            raise ValidationError("Invalid file selection.")
        selected_path = request.candidates[index]

        resolved_command: Command = replace(
            request.original_command,
            arguments=[selected_path if argument == request.query else argument
                       for argument in request.original_command.arguments],
        )
        # Go through the same ambiguity handling again if another argument
        # also needs selection. Quote paths so this command can be replayed.
        text = "/read {" + " ".join('"' + path + '"' for path in resolved_command.arguments) + "}"
        if resolved_command.prompt:
            text += "\n" + resolved_command.prompt
        return self.chat(session=session, text=text, on_chunk=on_chunk)

    def _run_tool_result(
        self,
        *,
        session: Session,
        command: Command,
        tool_result: ToolResult,
        text: str,
        on_chunk: Callable[[str], None] | None,
    ) -> ChatServiceResult:
        session.add_user(text, context=tool_result.requires_llm)

        for path, content in tool_result.metadata.files_read:
            session.remember_file(path, content)

        if not tool_result.requires_llm:
            # Deterministic display output (plain /read, /search, /git)
            # is shown to the user, but the raw dump never enters the
            # persisted model context -- that would silently
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
            on_chunk=on_chunk,
        )

    def _generate(
        self,
        *,
        session: Session,
        command: Command | None,
        tool_result: ToolResult | None,
        on_chunk: Callable[[str], None] | None,
    ) -> ChatServiceResult:
        expected_contents = self._overwrite.snapshot(command, tool_result)
        llm_response = self._llm.generate(
            session=session,
            tool_result=tool_result,
            on_chunk=on_chunk,
        )

        response = llm_response.content

        if command is not None:
            request = self._overwrite.create_request(command, response, expected_contents)

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
