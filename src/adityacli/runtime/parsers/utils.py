from __future__ import annotations

import shlex


def tokenize(prompt: str) -> list[str]:
    return shlex.split(prompt)


def strip_command(
    tokens: list[str],
    commands: tuple[str, ...],
) -> list[str]:

    if tokens and tokens[0].lower() in commands:
        return tokens[1:]

    return tokens


def normalize_prepositions(
    tokens: list[str],
) -> list[str]:
    """
    Remove natural-language filler words.

    move a.py to src/
    move a.py into src/
    copy a.py over backup/
    """

    fillers = {
        "to",
        "into",
        "in",
        "onto",
        "over",
    }

    return [
        token
        for token in tokens
        if token.lower() not in fillers
    ]