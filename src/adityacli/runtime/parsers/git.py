from __future__ import annotations

from .base import Parser
from ..parser_models import RuntimePlan, RuntimeStep


class GitParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:
        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="git_status",
                    arguments={
                        "command": prompt,
                    },
                )
            ]
        )