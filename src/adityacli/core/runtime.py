from config import AppConfig
from core.models import Message, Role
from core.parser import Parser
from core.session import Session
from llm.client import LLMClient


class Runtime:
    """Application runtime."""

    def __init__(
        self,
        config: AppConfig,
        client: LLMClient,
    ) -> None:
        self._config = config
        self._client = client
        self._parser = Parser()
        self._session = Session()

    @property
    def session(self) -> Session:
        return self._session

    def chat(self, text: str) -> str:
        command = self._parser.parse(text)

        if command is None:
            prompt = text
        else:
            prompt = text

        self._session.add_user(prompt)

        response = self._client.generate(self._session.messages)

        self._session.add_assistant(response)

        return response

    def clear(self) -> None:
        self._session.clear()

    def add_system_prompt(self, prompt: str) -> None:
        self._session.add_system(prompt)