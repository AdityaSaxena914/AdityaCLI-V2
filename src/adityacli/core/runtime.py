from collections.abc import Callable
import threading
from contextlib import contextmanager
from adityacli.core.operations import Operation
from adityacli.exceptions import ValidationError

from adityacli.config import AppConfig
from adityacli.core.models import (
    LLMResponse,
    OverwriteRequest,
    PendingSelectionRequest,
    RuntimeResult,
    ResponseStats,
)
from adityacli.core.parser import Parser
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.services.chat_service import (
    ChatService,
)


class Runtime:
    """Application runtime."""

    def __init__(
        self,
        *,
        config: AppConfig,
        parser: Parser,
        store: SessionStore,
        chat_service: ChatService,
        continue_session: bool = False,
    ) -> None:
        
        self._config: AppConfig = config
        self._parser: Parser = parser
        self._store: SessionStore = store
        self._chat_service: ChatService = chat_service

        self._last_response: LLMResponse | None = None
        self._operation: Operation | None = None
        self._interaction_lock = threading.Lock()

        self._continued_session: bool = (
            continue_session and self._store.exists
        )

        if self._continued_session:
            self._session = Session(
                self._store,
                max_read_tokens=config.lmstudio.context_window // 4,
            )
            self._session.load()
        else:
            self._store.clear(
                model=config.lmstudio.model,
                context_window=config.lmstudio.context_window,
            )

            self._session: Session = Session(
                self._store,
                max_read_tokens=config.lmstudio.context_window // 4,
            )

    @property
    def session(self) -> Session:
        return self._session

    def select_model(self, model_id: str) -> bool:
        """Keep archived history visible, but reset active prompt context."""
        changed = self._session.activate_model(model_id)
        if changed:
            self._last_response = None
        return changed

    def chat(
        self,
        text: str,
        *,
        on_chunk: Callable[[str], None] | None = None,
    ) -> RuntimeResult:
        
        with self._interaction():
            self._last_response = None
            service_result = self._chat_service.chat(
                session=self._session,
                text=text,
                on_chunk=on_chunk,
            )

            self._last_response = service_result.llm_response

        return service_result.result

    @contextmanager
    def _interaction(self):
        if not self._interaction_lock.acquire(blocking=False):
            raise ValidationError("An interaction is already running.")
        operation = self._operation = Operation(self._config.lmstudio.timeout)
        try:
            with operation.activate():
                yield
        finally:
            self._operation = None
            self._interaction_lock.release()

    def cancel_current(self) -> None:
        if self._operation is not None:
            self._operation.cancel()

    def confirm_overwrite(
        self,
        request: OverwriteRequest,
    ) -> None:
        with self._interaction():
            self._chat_service.confirm_overwrite(request)
            try:
                for path, content in request.files.items():
                    self._session.remember_file(path, content)
                self._session.add_assistant("Applied changes to: " + ", ".join(request.files), context=False)
            except Exception as exc:
                raise ValidationError("Files were applied, but session recording failed. Reread the files before continuing; do not apply the proposal again.") from exc

    def cancel_overwrite(self, request: OverwriteRequest) -> None:
        self._session.add_assistant("Cancelled changes to: " + ", ".join(request.files), context=False)

    def confirm_read_selection(
        self,
        request: PendingSelectionRequest,
        index: int,
        *,
        on_chunk: Callable[[str], None] | None = None,
    ) -> RuntimeResult:
        with self._interaction():
            self._last_response = None
            service_result = self._chat_service.resolve_selection(
                session=self._session,
                request=request,
                index=index,
                on_chunk=on_chunk,
            )

            self._last_response = service_result.llm_response

        return service_result.result

    def clear(self) -> None:
        with self._interaction():
            self._clear()

    def _clear(self) -> None:
        system_messages = [
            message.content
            for message in self._session.messages
            if message.role.value == "system"
        ]

        self._session.clear(
            model=self._config.lmstudio.model,
            context_window=self._config.lmstudio.context_window,
            system_prompts=system_messages,
        )
        self._last_response = None
        self._continued_session = False

    def add_system_prompt(
        self,
        prompt: str,
    ) -> None:
        self._session.add_system(prompt)

    @property
    def parser(self) -> Parser:
        return self._parser

    @property
    def last_response(self) -> LLMResponse | None:
        """Return the last LLM response metadata."""
        return self._last_response

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def continued_session(self) -> bool:
        return self._continued_session


    def needs_followup(
        self,
        text: str,
    ) -> str | None:
        return self._chat_service.needs_followup(text)

    def confirmation_message(
        self,
        request: OverwriteRequest,
        command_text: str,
    ) -> str:
        return self._chat_service.confirmation_message(
            request,
            command_text,
        )


    @property
    def response_stats(
        self,
    ) -> ResponseStats | None:
        if self._last_response is None:
            return None

        response = self._last_response

        speed = (
            response.completion_tokens
            / response.elapsed_seconds
            if response.elapsed_seconds > 0
            else 0.0
        )

        return ResponseStats(
            model=response.model,
            elapsed_seconds=response.elapsed_seconds,
            completion_tokens=response.completion_tokens,
            speed=speed,
        )
