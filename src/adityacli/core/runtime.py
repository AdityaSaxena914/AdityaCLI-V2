from adityacli.config import AppConfig
from collections.abc import Iterator
from adityacli.core.models import (
    LLMResponse,
    OverwriteRequest,
    RuntimeResult,
    ResponseStats,
)
from adityacli.core.parser import Parser
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.services.chat_service import (
    ChatService,
)
from adityacli.core.token_budget import TokenBudget
from adityacli.core.workspace_guard import WorkspaceGuard

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

        self._budget: TokenBudget = TokenBudget(
            config.lmstudio.context_window,
        )

        self._last_response: LLMResponse | None = None
        self._guard: WorkspaceGuard = WorkspaceGuard(config)

        self._continued_session: bool = (
            continue_session and self._store.exists
        )

        if self._continued_session:
            self._session = Session(self._store)
            self._session.load()
        else:
            self._store.clear(
                model=config.lmstudio.model,
                context_window=config.lmstudio.context_window,
            )

            self._session: Session = Session(self._store)

    @property
    def session(self) -> Session:
        return self._session

    def chat(
        self,
        text: str,
    ) -> RuntimeResult:
        
        service_result = self._chat_service.chat(
            session=self._session,
            text=text,
        )

        self._last_response = service_result.llm_response

        return service_result.result

    def chat_stream(
        self,
        text: str,
    ) -> Iterator[str]:
        for chunk in self._chat_service.chat_stream(
            session=self._session,
            text=text,
        ):
            yield chunk

        self._last_response = self._chat_service.last_response


    def confirm_overwrite(
        self,
        request: OverwriteRequest,
    ) -> None:
        self._chat_service.confirm_overwrite(request)

    def clear(self) -> None:
        system_messages = [
            message.content
            for message in self._session.messages
            if message.role.value == "system"
        ]

        self._session.clear(
            model=self._config.lmstudio.model,
            context_window=self._config.lmstudio.context_window,
        )

        for prompt in system_messages:
            self._session.add_system(prompt)

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


    @property
    def workspace_guard(self) -> WorkspaceGuard:
        return self._guard