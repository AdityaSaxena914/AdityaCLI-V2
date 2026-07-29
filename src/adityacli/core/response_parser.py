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
        paths: list[str],
    ) -> dict[str, str]:
        content = self._strip_code_fence(response)
        content = self._strip_file_header(content)

        if len(paths) != 1:
            raise InvalidResponseError(
                "Multiple file generation is not yet supported."
            )

        return {
            paths[0]: content.strip(),
        }

    def parse_edit_response(self, response: str) -> str:
        """
        Parse an /edit response.

        The model is instructed to return only the
        complete updated file contents.
        """

        content = self._strip_code_fence(response)
        content = self._strip_file_header(content)

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

    @staticmethod
    def _strip_file_header(
        content: str,
    ) -> str:
        import re

        content = re.sub(
            r"^=== FILE:.*?===\s*\n?",
            "",
            content,
            flags=re.MULTILINE,
        )

        content = re.sub(
            r"^[A-Za-z0-9_.-]+\s*=+\s*\n?",
            "",
            content,
            flags=re.MULTILINE,
        )

        return content.strip()