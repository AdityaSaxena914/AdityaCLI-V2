from adityacli.config import AppConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.models import (
    ChatResponse,
    LLMResponse,
    OverwriteRequest,
    RuntimeResult,
    Tool,
)
from adityacli.core.parser import Parser
from adityacli.core.response_parser import ResponseParser
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.llm.client import LLMClient
from adityacli.tools.registry import ToolRegistry
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService


class Runtime:
    """Application runtime."""

    def __init__(
        self,
        config: AppConfig,
        client: LLMClient,
        registry: ToolRegistry,
        *,
        continue_session: bool = False,
    ) -> None:
        self._config = config
        self._llm_service = LLMService(
            client=client,
            prompt_builder=self._prompt_builder,
        )
        self._parser = Parser()
        self._registry = registry

        self._command_service = CommandService(
            parser=self._parser,
            registry=self._registry,
        )
        self._response_parser = ResponseParser()
        self._file_manager = FileManager(config)

        self._prompt_builder = PromptBuilder()
        self._last_response: LLMResponse | None = None

        self._store = SessionStore(
            config.workspace.root,
        )

        self._continued_session = (
            continue_session and self._store.exists
        )

        self._overwrite_service = OverwriteService(
            parser=self._response_parser,
            file_manager=self._file_manager,
            store=self._store,
        )

        if self._continued_session:
            self._session = Session(self._store)
            self._session.load()
        else:
            self._store.clear(
                model=config.lmstudio.model,
                context_window=config.lmstudio.context_window,
            )

            self._session = Session(self._store)

    @property
    def session(self) -> Session:
        return self._session

    def chat(
        self,
        text: str,
    ) -> RuntimeResult:
        
        command = self._command_service.parse(text)

        tool_result = None

        if command is None:
            self._session.add_user(text)
        else:
            tool_result = self._command_service.execute(command)
            
            if not tool_result.requires_llm:
                self._session.add_user(text)
                self._session.add_assistant(tool_result.prompt)

                self._store.flush_memory()
                return ChatResponse(tool_result.prompt)

            for cached_file in tool_result.metadata.files_read:
                self._store.cache_file(
                    path=cached_file.path,
                    content=cached_file.content,
                )

            self._session.add_user(text)

        llm_response = self._llm_service.generate(
            session=self._session,
            tool_result=tool_result,
        )

        self._last_response = llm_response

        response = llm_response.content

        if command is None:
            self._store.flush_memory()
            return ChatResponse(response)

        request = self._overwrite_service.create_request(
            command,
            response,
        )

        if request is not None:
            self._store.flush_memory()
            return request

        self._store.flush_memory()

        return ChatResponse(response)

    def confirm_overwrite(
        self,
        request: OverwriteRequest,
    ) -> None:
        self._overwrite_service.confirm(request)

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
        command = self._parser.parse(text)

        if command is None:
            return None

        if command.tool is Tool.WRITE and "\n" not in text:
            return "What would you like to generate?"

        if command.tool is Tool.EDIT and "\n" not in text:
            return "What would you like to change?"

        return None