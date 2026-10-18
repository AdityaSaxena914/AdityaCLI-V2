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
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            lineterm="",
        )
    )

    # remove --- and +++ headers
    if len(diff) >= 2:
        diff = diff[2:]

    lines = []
    for line in diff:
        if line.startswith(("+", "-", " ")) and not line.endswith(("\n", "\r")):
            lines.extend((line, "\\ No newline at end of file"))
        else:
            lines.append(line.rstrip("\r\n"))
    return "\n".join(lines)
