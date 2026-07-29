from pathlib import Path

import pytest

from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.models import (
    ChatResponse,
    Command,
    OverwriteRequest,
    Role,
    Tool,
)
from adityacli.core.runtime import Runtime
from adityacli.core.models import (
    ToolMetadata,
    ToolResult,
)


class FakeLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        return self.response


class FakeRegistry:
    def __init__(self, prompt: str = "tool prompt") -> None:
        self.prompt = prompt
        self.calls = 0
        self.last_command = None

    def execute(self, command: Command) -> str:
        self.calls += 1
        self.last_command = command
        return ToolResult(
            prompt=self.prompt,
            metadata=ToolMetadata(),
        )


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        workspace=WorkspaceConfig(root=tmp_path),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )


def test_plain_chat(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient("Hello!"),
        registry=FakeRegistry(),
    )

    result = runtime.chat("Hi")

    assert isinstance(result, ChatResponse)
    assert result.content == "Hello!"


def test_session_is_updated(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient("Reply"),
        registry=FakeRegistry(),
    )

    runtime.chat("Hello")

    messages = runtime.session.messages

    assert len(messages) == 2
    assert messages[0].role is Role.USER
    assert messages[1].role is Role.ASSISTANT


def test_registry_is_used(config: AppConfig) -> None:
    registry = FakeRegistry("expanded prompt")

    runtime = Runtime(
        config=config,
        client=FakeLLMClient("Answer"),
        registry=registry,
    )

    runtime.chat("/search main")

    assert registry.calls == 1
    assert registry.last_command.tool is Tool.SEARCH


def test_write_returns_overwrite_request(config: AppConfig) -> None:
    llm = FakeLLMClient(
        """
=== FILE: hello.py ===
print("hello")
""".strip()
    )

    runtime = Runtime(
        config=config,
        client=llm,
        registry=FakeRegistry(),
    )

    result = runtime.chat("/write {hello.py}")

    assert isinstance(result, OverwriteRequest)
    assert result.files == {
        "hello.py": 'print("hello")'
    }


def test_edit_returns_overwrite_request(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient("print('updated')"),
        registry=FakeRegistry(),
    )

    result = runtime.chat("/edit hello.py")

    assert isinstance(result, OverwriteRequest)
    assert result.files == {
        "hello.py": "print('updated')"
    }


def test_confirm_overwrite(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient(""),
        registry=FakeRegistry(),
    )

    runtime.confirm_overwrite(
        OverwriteRequest(
            {
                "a.txt": "hello"
            }
        )
    )

    assert (
        config.workspace.root / "a.txt"
    ).read_text() == "hello"


def test_clear_session(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient("Reply"),
        registry=FakeRegistry(),
    )

    runtime.chat("Hello")

    assert runtime.session.messages

    runtime.clear()

    assert runtime.session.messages == []


def test_add_system_prompt(config: AppConfig) -> None:
    runtime = Runtime(
        config=config,
        client=FakeLLMClient(""),
        registry=FakeRegistry(),
    )

    runtime.add_system_prompt("You are helpful.")

    assert len(runtime.session.messages) == 1
    assert runtime.session.messages[0].role is Role.SYSTEM
    assert runtime.session.messages[0].content == "You are helpful."