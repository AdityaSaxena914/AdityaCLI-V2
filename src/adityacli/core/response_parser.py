import re

from adityacli.exceptions import InvalidResponseError, MalformedGenerationError


_FILE_HEADER = re.compile(
    r"^=== FILE:\s*(.+?)\s*===\s*$",
    re.MULTILINE,
)

_END_OF_FILE_SENTINEL = "=== END FILE ==="

# Loop-detection: if the same N-line block repeats this many times
# consecutively, treat it as a generation loop rather than intended
# content (catches the repeated CSS/media-query symptom directly).
_REPEAT_WINDOW_LINES = 6
_REPEAT_THRESHOLD = 4


class ResponseParser:
    """Parses deterministic LLM responses."""

    def parse_write_response(
        self,
        response: str,
        paths: list[str],
    ) -> dict[str, str]:
        content = self._strip_sentinel(response)
        content = self._strip_code_fence(content)
        content = self._strip_file_header(content)
        content = content.strip()

        if len(paths) != 1:
            raise InvalidResponseError(
                "Multiple file generation is not yet supported."
            )

        self._validate(content)

        return {
            paths[0]: content,
        }

    def parse_edit_response(self, response: str) -> str:
        """
        Parse an /edit response.

        The model is instructed to return only the
        complete updated file contents.
        """

        content = self._strip_sentinel(response)
        content = self._strip_code_fence(content)
        content = self._strip_file_header(content)
        content = content.strip()

        if not content:
            raise InvalidResponseError(
                "Empty response from the language model."
            )

        self._validate(content)

        return content

    @staticmethod
    def _strip_sentinel(content: str) -> str:
        return content.replace(_END_OF_FILE_SENTINEL, "").rstrip()

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        """
        Remove a single outer Markdown code fence if present.

        The opening fence line is dropped even when the closing fence
        is missing (truncated generation) -- otherwise a truncated
        response leaks a literal ```lang line into the written file.
        """

        content = content.strip()

        if not content.startswith("```"):
            return content

        lines = content.splitlines()

        if len(lines) < 2:
            return content

        body = lines[1:]

        if body and body[-1].strip().startswith("```"):
            body = body[:-1]

        return "\n".join(body).strip()

    @staticmethod
    def _strip_file_header(
        content: str,
    ) -> str:
        content = re.sub(
            r"^=== FILE:.*?===\s*\n?",
            "",
            content,
            flags=re.MULTILINE,
        )

        return content.strip()

    @staticmethod
    def _validate(content: str) -> None:
        if not content:
            raise MalformedGenerationError(
                "Empty response from the language model."
            )

        opens = content.count("{")
        closes = content.count("}")

        if opens != closes:
            raise MalformedGenerationError(
                f"Unbalanced braces ({opens} open / {closes} close) -- "
                "generation is malformed or was cut mid-block."
            )

        lines = content.splitlines()
        window = _REPEAT_WINDOW_LINES

        i = 0
        while i + window * _REPEAT_THRESHOLD <= len(lines):
            block = tuple(lines[i : i + window])

            repeat_count = 1
            j = i + window

            while (
                j + window <= len(lines)
                and tuple(lines[j : j + window]) == block
            ):
                repeat_count += 1
                j += window

            if repeat_count >= _REPEAT_THRESHOLD:
                raise MalformedGenerationError(
                    f"Detected a {repeat_count}x repeated {window}-line "
                    f"block starting at line {i + 1} -- generation "
                    "loop, rejecting output."
                )

            i += window
