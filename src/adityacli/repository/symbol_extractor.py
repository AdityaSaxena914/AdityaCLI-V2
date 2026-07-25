from __future__ import annotations

import re


class SymbolExtractor:
    """Extract repository symbols from natural-language prompts."""

    _PATTERN = re.compile(
        r"\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\b"
    )

    def extract(
        self,
        prompt: str,
    ) -> str | None:

        matches = list(
            self._PATTERN.finditer(prompt)
        )

        for match in reversed(matches):

            symbol = match.group(1)

            if "." in symbol:
                return symbol

            if "_" in symbol:
                return symbol

            if (
                len(symbol) > 1
                and symbol[0].isupper()
                and any(
                    c.isupper()
                    for c in symbol[1:]
                )
            ):
                return symbol

        return None