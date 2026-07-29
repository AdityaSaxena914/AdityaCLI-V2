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
        self._client = client
        self._registry = registry

        self._parser = Parser()
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

        if self._continued_session:
            self._session = Session(self._store)
            self._session.load()
        else:
            self._store.clear(
                model=config.lmstudio.model,
                context_window=65536,
            )

            self._session = Session(self._store)

    @property
    def session(self) -> Session:
        return self._session

    def chat(
        self,
        text: str,
    ) -> RuntimeResult:
        command = self._parser.parse(text)
        tool_result = None

        if command is None:
            self._session.add_user(text)
        else:
            tool_result = self._registry.execute(command)
            
            if not tool_result.requires_llm:
                return ChatResponse(tool_result.prompt)

            for cached_file in tool_result.metadata.files_read:
                self._store.cache_file(
                    path=cached_file.path,
                    content=cached_file.content,
                )

            self._session.add_user(text)

        messages = self._prompt_builder.build(
            messages=self._session.messages,
            tool_result=tool_result,
        )

        llm_response = self._client.generate(messages)

        self._last_response = llm_response

        response = llm_response.content

        self._session.add_assistant(response)

        if command is None:
            return ChatResponse(response)

        if command.tool is Tool.WRITE:
            files = self._response_parser.parse_write_response(
                response=response,
                paths=command.arguments,
            )

            return OverwriteRequest(files)

        if command.tool is Tool.EDIT:
            content = self._response_parser.parse_edit_response(
                response,
            )

            return OverwriteRequest(
                {
                    command.arguments[0]: content,
                }
            )

        return ChatResponse(response)

    def confirm_overwrite(
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

    def clear(self) -> None:
        system_messages = [
            message.content
            for message in self._session.messages
            if message.role.value == "system"
        ]

        self._session.clear(
            model=self._config.lmstudio.model,
            context_window=65536,
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