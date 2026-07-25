from __future__ import annotations

import re
from pathlib import Path


class PathExtractor:
    """Extract workspace file paths from free-form text."""

    _PATTERN = re.compile(
        r"((?:[\w.-]+[/\\])+[\w.-]+|\b[\w.-]+\.(?:py|md|txt|json|yaml|yml|toml|ini|cfg|lock)\b)"
    )

    def extract(
        self,
        text: str,
    ) -> Path | None:

        match = self._PATTERN.search(text)

        if match is None:
            return None

        return Path(match.group(1))