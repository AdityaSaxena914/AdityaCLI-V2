from pathlib import Path

import pytest
from typing import cast
from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.models import (
    ChatResponse,
    LLMResponse,
    OverwriteRequest,
)
from adityacli.services.chat_service import (
    ChatService,
    ChatServiceResult,
)
from adityacli.core.parser import Parser
from adityacli.core.runtime import Runtime
from adityacli.core.session_store import SessionStore
from adityacli.core.session import Session


class FakeChatService:
    def __init__(self) -> None:
        self.chat_calls: int = 0
        self.overwrite_calls: int = 0

    def chat(
        self,
        *,
        session: Session,
        text: str,
    ) -> ChatServiceResult:
        del session
        del text
        self.chat_calls += 1

        return ChatServiceResult(
            result=ChatResponse("reply"),
            llm_response=LLMResponse(
                content="reply",
                model="test",
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                elapsed_seconds=2.0,
            ),
        )

    def confirm_overwrite(
        self,
        request: OverwriteRequest,
    ) -> None:
        del request
        self.overwrite_calls += 1

    def needs_followup(
        self,
        text: str,
    ) -> str | None:
        del text
        return None

    def confirmation_message(
        self,
        request: OverwriteRequest,
        command_text: str,
    ) -> str:
        del request
        del command_text
        return "confirm?"


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    config = AppConfig(
        workspace=WorkspaceConfig(root=tmp_path),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )

    return Runtime(
        config=config,
        parser=Parser(),
        store=SessionStore(tmp_path),
        chat_service=cast(
            ChatService,
            cast(
                object,
                FakeChatService(),
            ),
        ),
    )


def test_chat(runtime: Runtime) -> None:
    result = runtime.chat("hello")

    assert isinstance(result, ChatResponse)
    assert result.content == "reply"


def test_add_system_prompt(runtime: Runtime) -> None:
    runtime.add_system_prompt("system")

    assert runtime.session.messages[0].content == "system"


def test_clear(runtime: Runtime) -> None:
    runtime.add_system_prompt("system")
    runtime.clear()

    assert len(runtime.session.messages) == 1
    assert runtime.session.messages[0].content == "system"


def test_response_stats(runtime: Runtime) -> None:
    _=runtime.chat("hello")

    stats = runtime.response_stats

    assert stats is not None
    assert stats.model == "test"
    assert stats.speed == 10.0