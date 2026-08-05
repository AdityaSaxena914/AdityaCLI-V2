import pytest

from adityacli.core.response_parser import ResponseParser
from adityacli.exceptions import InvalidResponseError


@pytest.fixture
def parser() -> ResponseParser:
    return ResponseParser()


def test_parse_single_file(parser: ResponseParser) -> None:
    response = """
=== FILE: src/main.py ===
print("hello")
""".strip()

    result = parser.parse_write_response(
        response=response,
        paths=["src/main.py"],
    )

    assert result == {
        "src/main.py": 'print("hello")',
    }


def test_multiple_files_not_supported(
    parser: ResponseParser,
) -> None:
    with pytest.raises(InvalidResponseError):
        _=parser.parse_write_response(
            response="",
            paths=["a.py", "b.py"],
        )


def test_parse_edit_response(
    parser: ResponseParser,
) -> None:
    content = parser.parse_edit_response(
        "print('updated')"
    )

    assert content == "print('updated')"


def test_parse_edit_response_empty(
    parser: ResponseParser,
) -> None:
    with pytest.raises(InvalidResponseError):
        _=parser.parse_edit_response("   \n\t")