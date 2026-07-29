import re

from adityacli.exceptions import InvalidResponseError


_FILE_HEADER = re.compile(
    r"^=== FILE:\s*(.+?)\s*===\s*$",
    re.MULTILINE,
)


class ResponseParser:
    """Parses deterministic LLM responses."""

    def parse_write_response(
        self,
        response: str,
        expected_files: list[str],
    ) -> dict[str, str]:
        """
        Parse a multi-file /write response.

        Expected format:

        === FILE: path ===
        <contents>

        === FILE: another/path ===
        <contents>
        """

        expected = set(expected_files)
        parsed: dict[str, str] = {}

        matches = list(_FILE_HEADER.finditer(response))

        if not matches:
            raise InvalidResponseError(
                "No file sections were found in the response."
            )

        for index, match in enumerate(matches):
            path = match.group(1).strip()

            if path in parsed:
                raise InvalidResponseError(
                    f"Duplicate file section: {path}"
                )

            if path not in expected:
                raise InvalidResponseError(
                    f"Unexpected file returned: {path}"
                )

            start = match.end()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(response)

            content = self._strip_code_fence(
                response[start:end]
            )

            if not content:
                raise InvalidResponseError(
                    f"No content returned for {path}"
                )

            parsed[path] = content

        missing = expected.difference(parsed)

        if missing:
            raise InvalidResponseError(
                "Missing generated files: "
                + ", ".join(sorted(missing))
            )

        return parsed

    def parse_edit_response(self, response: str) -> str:
        """
        Parse an /edit response.

        The model is instructed to return only the
        complete updated file contents.
        """

        content = self._strip_code_fence(response)

        if not content:
            raise InvalidResponseError(
                "Empty response from the language model."
            )

        return content

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        """
        Remove a single outer Markdown code fence if present.
        """

        content = content.strip()

        if not content.startswith("```"):
            return content

        lines = content.splitlines()

        if len(lines) < 2:
            return content

        if not lines[-1].strip().startswith("```"):
            return content

        return "\n".join(lines[1:-1]).strip()