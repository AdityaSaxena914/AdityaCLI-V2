from __future__ import annotations

import shlex

from .base import Parser
from ..parser_models import RuntimePlan, RuntimeStep


class EditParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:
        tokens = shlex.split(prompt)

        if len(tokens) < 4:
            return RuntimePlan()

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="edit_file",
                    arguments={
                        "path": tokens[1],
                        "old_text": tokens[2],
                        "new_text": " ".join(tokens[3:]),
                    },
                )
            ]
        )