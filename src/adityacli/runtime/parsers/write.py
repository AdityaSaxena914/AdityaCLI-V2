from __future__ import annotations

from ..grammars import filesystem
from ..parser_models import RuntimePlan, RuntimeStep
from .base import Parser
from .utils import strip_command, tokenize


class WriteParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:

        tokens = strip_command(
            tokenize(prompt),
            filesystem.WRITE,
        )

        if len(tokens) < 2:
            return RuntimePlan()

        _, _, remainder = prompt.partition(" ")

        path, _, content = remainder.partition(" ")

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="write_file",
                    arguments={
                        "path": path,
                        "content": content,
                    },
                )
            ]
        )