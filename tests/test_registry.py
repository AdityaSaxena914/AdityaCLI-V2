from pathlib import Path

import pytest

from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.models import Command, Tool
from adityacli.tools.registry import ToolRegistry
from adityacli.exceptions import InvalidCommandError



@pytest.fixture
def registry(tmp_path: Path) -> ToolRegistry:
    config = AppConfig(
        workspace=WorkspaceConfig(root=tmp_path),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )
    return ToolRegistry(config)


@pytest.mark.parametrize(
    "tool",
    [
        Tool.READ,
        Tool.WRITE,
        Tool.EDIT,
        Tool.SEARCH,
        Tool.WEB,
        Tool.GIT,
    ],
)
def test_registry_has_tool(
    registry: ToolRegistry,
    tool: Tool,
) -> None:
    assert registry.get(tool) is not None


def test_execute_read(
    registry: ToolRegistry,
    tmp_path: Path,
) -> None:
    (tmp_path / "hello.txt").write_text("hello")

    command = Command(
        tool=Tool.READ,
        arguments=["hello.txt"],
        prompt="Explain.",
    )

    result = registry.execute(command)

    assert "hello" in result.prompt
    assert len(result.metadata.files_read) == 1

    cached = result.metadata.files_read[0]

    assert cached.path == "hello.txt"
    assert cached.content == "hello"
    assert cached.sha256


def test_execute_unknown_tool(registry: ToolRegistry) -> None:
    class FakeTool:
        pass

    command = Command(
        tool=FakeTool(),  # type: ignore[arg-type]
        arguments=[],
        prompt="",
    )

    with pytest.raises(InvalidCommandError):
        registry.execute(command)