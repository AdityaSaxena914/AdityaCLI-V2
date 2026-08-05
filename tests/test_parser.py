import pytest

from adityacli.core.models import Tool
from adityacli.core.parser import Parser
from adityacli.exceptions import (
    InvalidCommandError,
    InvalidSyntaxError,
)


@pytest.fixture
def parser() -> Parser:
    return Parser()


def test_plain_chat_returns_none(parser: Parser) -> None:
    assert parser.parse("Hello") is None


def test_parse_read_command(parser: Parser) -> None:
    command = parser.parse("/read src/main.py")

    assert command is not None
    assert command.tool is Tool.READ
    assert command.arguments == ["src/main.py"]
    assert command.prompt == ""


def test_parse_write_command(parser: Parser) -> None:
    command = parser.parse("/write {src/main.py}")

    assert command is not None
    assert command.tool is Tool.WRITE
    assert command.arguments == ["src/main.py"]


def test_parse_multiple_write_files(parser: Parser) -> None:
    command = parser.parse(
        "/write {index.html style.css script.js}"
    )

    assert command is not None

    assert command.arguments == [
        "index.html",
        "style.css",
        "script.js",
    ]


def test_parse_git_command(parser: Parser) -> None:
    command = parser.parse("/git {status}")

    assert command is not None
    assert command.tool is Tool.GIT
    assert command.arguments == ["status"]


def test_prompt_after_command(parser: Parser) -> None:
    command = parser.parse(
        "/read src/main.py\n" + "Explain this implementation."
    )

    assert command is not None
    assert command.prompt == "Explain this implementation."


def test_multiline_prompt(parser: Parser) -> None:
    command = parser.parse(
        "/edit src/main.py\n" + "Refactor this.\n" + "Keep public API unchanged."
    )

    assert command is not None
    assert command.prompt == (
        "Refactor this.\n"
        "Keep public API unchanged."
    )


def test_unknown_command(parser: Parser) -> None:
    with pytest.raises(InvalidCommandError):
        _=parser.parse("/foobar")


def test_write_requires_braces(parser: Parser) -> None:
    with pytest.raises(InvalidSyntaxError):
        _=parser.parse("/write src/main.py")


def test_git_requires_braces(parser: Parser) -> None:
    with pytest.raises(InvalidSyntaxError):
        _=parser.parse("/git status")


def test_empty_braces(parser: Parser) -> None:
    command = _=parser.parse("/write {}")

    assert command is not None
    assert command.arguments == []


def test_whitespace_is_trimmed(parser: Parser) -> None:
    command = parser.parse(
        "   /read    src/main.py    "
    )

    assert command is not None
    assert command.arguments == ["src/main.py"]


def test_command_without_arguments(parser: Parser) -> None:
    command = parser.parse("/search")

    assert command is not None
    assert command.tool is Tool.SEARCH
    assert command.arguments == []