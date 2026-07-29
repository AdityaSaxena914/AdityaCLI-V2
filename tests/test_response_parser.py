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
        expected_files=["src/main.py"],
    )

    assert result == {
        "src/main.py": 'print("hello")',
    }


def test_parse_multiple_files(parser: ResponseParser) -> None:
    response = """
=== FILE: a.py ===
print("a")

=== FILE: b.py ===
print("b")
""".strip()

    result = parser.parse_write_response(
        response=response,
        expected_files=["a.py", "b.py"],
    )

    assert result == {
        "a.py": 'print("a")',
        "b.py": 'print("b")',
    }


def test_missing_file(parser: ResponseParser) -> None:
    response = """
=== FILE: a.py ===
print("a")
""".strip()

    with pytest.raises(InvalidResponseError):
        parser.parse_write_response(
            response=response,
            expected_files=["a.py", "b.py"],
        )


def test_unexpected_file(parser: ResponseParser) -> None:
    response = """
=== FILE: c.py ===
print("c")
""".strip()

    with pytest.raises(InvalidResponseError):
        parser.parse_write_response(
            response=response,
            expected_files=["a.py"],
        )


def test_duplicate_file(parser: ResponseParser) -> None:
    response = """
=== FILE: a.py ===
one

=== FILE: a.py ===
two
""".strip()

    with pytest.raises(InvalidResponseError):
        parser.parse_write_response(
            response=response,
            expected_files=["a.py"],
        )


def test_empty_file_contents(parser: ResponseParser) -> None:
    response = """
=== FILE: a.py ===
""".strip()

    with pytest.raises(InvalidResponseError):
        parser.parse_write_response(
            response=response,
            expected_files=["a.py"],
        )


def test_no_headers(parser: ResponseParser) -> None:
    with pytest.raises(InvalidResponseError):
        parser.parse_write_response(
            response="print('hello')",
            expected_files=["a.py"],
        )


def test_parse_edit_response(parser: ResponseParser) -> None:
    content = parser.parse_edit_response(
        "print('updated')"
    )

    assert content == "print('updated')"


def test_parse_edit_response_empty(parser: ResponseParser) -> None:
    with pytest.raises(InvalidResponseError):
        parser.parse_edit_response("   \n\t")