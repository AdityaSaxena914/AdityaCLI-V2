from __future__ import annotations

from difflib import unified_diff


def build_diff(
    original: str,
    updated: str,
) -> str:
    """
    Return a clean unified diff for terminal display.
    """

    diff = list(
        unified_diff(
            original.splitlines(),
            updated.splitlines(),
            lineterm="",
        )
    )

    # remove --- and +++ headers
    if len(diff) >= 2:
        diff = diff[2:]

    return "\n".join(diff)