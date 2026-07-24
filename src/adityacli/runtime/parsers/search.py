from __future__ import annotations

import shlex

from .base import Parser
from ..parser_models import RuntimePlan, RuntimeStep


class SearchParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:
        tokens = shlex.split(prompt)

        if len(tokens) < 2:
            return RuntimePlan()

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="workspace_search",
                    arguments={
                        "query": tokens[-1],
                    },
                )
            ]
        )