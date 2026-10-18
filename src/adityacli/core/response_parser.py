import json
import re
from pathlib import Path

from adityacli.exceptions import InvalidResponseError, MalformedGenerationError


_LEADING_HEADER = re.compile(r"\A=== FILE:[^\r\n]+===[ \t]*(?:\r?\n|$)")
_PROSE_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst"}


class ResponseParser:
    """Parses deterministic LLM responses."""

    def parse_write_response(
        self,
        response: str,
        paths: list[str],
    ) -> dict[str, str]:
        if len(paths) != 1:
            raise InvalidResponseError(
                "Multiple file generation is not yet supported."
            )

        content = self._unwrap(response, paths[0])
        self._validate(content, paths[0])

        return {
            paths[0]: content,
        }

    def parse_edit_response(self, response: str, path: str | None = None) -> str:
        """
        Parse an /edit response.

        The model is instructed to return only the
        complete updated file contents.
        """

        content = self._unwrap(response, path)
        if not content.strip():
            raise InvalidResponseError(
                "Empty response from the language model."
            )

        self._validate(content, path)

        return content

    def _unwrap(self, content: str, path: str | None) -> str:
        # Markdown fences and header-looking lines are legitimate prose.
        if path is not None and Path(path).suffix.lower() in _PROSE_SUFFIXES:
            return content
        return self._strip_file_header(self._strip_code_fence(content))

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        """
        Remove only a complete outer Markdown fence, preserving its body.
        """

        if not content.startswith("```"):
            return content

        lines = content.splitlines(keepends=True)
        if not re.fullmatch(r"```[\w.+-]*[ \t]*", lines[0].rstrip("\r\n")):
            return content
        # Blank lines outside the closing fence are wrapper whitespace.
        while len(lines) > 1 and not lines[-1].strip():
            lines.pop()
        if len(lines) < 2 or lines[-1].strip() != "```":
            raise MalformedGenerationError("Unclosed Markdown fence in generated output.")
        return "".join(lines[1:-1])

    @staticmethod
    def _strip_file_header(
        content: str,
    ) -> str:
        return _LEADING_HEADER.sub("", content, count=1)

    @staticmethod
    def _validate(content: str, path: str | None = None) -> None:
        if not content.strip():
            raise MalformedGenerationError(
                "Empty response from the language model."
            )
        suffix = Path(path).suffix.lower() if path else ""
        try:
            if suffix == ".json":
                json.loads(content)
            elif suffix == ".py":
                compile(content, path or "<generated>", "exec")
        except (ValueError, SyntaxError) as exc:
            raise MalformedGenerationError(f"Generated {suffix} file is invalid: {exc}") from exc
