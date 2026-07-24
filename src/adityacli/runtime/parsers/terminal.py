from __future__ import annotations

from .base import Parser
from ..parser_models import RuntimePlan, RuntimeStep


class TerminalParser(Parser):

    def parse(self, prompt: str) -> RuntimePlan:
        command = prompt.partition(" ")[2].strip()

        if not command:
            return RuntimePlan()

        return RuntimePlan(
            steps=[
                RuntimeStep(
                    tool="terminal",
                    arguments={
                        "command": command,
                    },
                )
            ]
        )