from adityacli.config import AppConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.models import (
    ChatResponse,
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

        self._store = SessionStore(
            config.workspace.root,
        )

        if continue_session and self._store.exists:
            self._session = Session(self._store)
            self._session.load()
        else:
            self._store.clear()
            self._store.create(
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
            prompt = text
        else:
            tool_result = self._registry.execute(command)
            prompt = tool_result.prompt

        if tool_result is not None:
            for cached_file in tool_result.metadata.files_read:
                self._store.cache_file(
                    path=cached_file.path,
                    content=cached_file.content,
                )
        
        prompt = self._prompt_builder.build(
            messages=self._session.messages,
            tool_result=tool_result,
            user_input=text,
        )

        self._session.add_user(prompt)

        response = self._client.generate(
            self._session.messages,
        )

        self._session.add_assistant(response)

        if command is None:
            return ChatResponse(response)

        if command.tool is Tool.WRITE:
            files = self._response_parser.parse_write_response(
                response=response,
                expected_files=command.arguments,
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
        self._session.clear()

    def add_system_prompt(
        self,
        prompt: str,
    ) -> None:
        self._session.add_system(prompt)