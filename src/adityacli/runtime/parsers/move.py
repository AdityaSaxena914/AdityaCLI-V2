from __future__ import annotations

from ..grammars import filesystem
from ..parser_models import RuntimePlan, RuntimeStep
from .base import Parser
from .utils import (
    normalize_prepositions,
    strip_command,
    tokenize,
)


class MoveParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:

        tokens = normalize_prepositions(
            strip_command(
                tokenize(prompt),
                filesystem.MOVE,
            )
        )

        if len(tokens) < 2:
            return RuntimePlan()

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="move_file",
                    arguments={
                        "source": tokens[0],
                        "destination": tokens[1],
                    },
                )
            ]
        )