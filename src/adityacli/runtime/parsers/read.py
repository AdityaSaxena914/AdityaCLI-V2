from __future__ import annotations

from ..grammars import filesystem
from ..parser_models import RuntimePlan, RuntimeStep
from .base import Parser
from .utils import strip_command, tokenize


class ReadParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:

        tokens = strip_command(
            tokenize(prompt),
            filesystem.READ,
        )

        if not tokens:
            return RuntimePlan()

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="read_file",
                    arguments={
                        "path": tokens[0],
                    },
                )
            ]
        )