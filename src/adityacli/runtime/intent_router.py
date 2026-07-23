from __future__ import annotations

import re

from .models import (
    IntentResult,
    PipelineType,
)


class IntentRouter:
    """Deterministically route requests to execution pipelines."""

    _DETERMINISTIC_PATTERNS: dict[str, tuple[str, ...]] = {
        "read_file": (
            r"\bread\b",
            r"\bopen\b",
            r"\bshow\b",
            r"\bdisplay\b",
        ),
        "write_file": (
            r"\bwrite\b",
            r"\bcreate\b",
            r"\bsave\b",
        ),
        "edit_file": (
            r"\bedit\b",
            r"\breplace\b",
            r"\bmodify\b",
            r"\bupdate\b",
        ),
        "workspace_search": (
            r"\bsearch\b",
            r"\bfind\b",
            r"\blocate\b",
        ),
        "git_status": (
            r"\bgit\b",
            r"\bbranch\b",
            r"\bcommit\b",
            r"\bstatus\b",
        ),
        "terminal": (
            r"\brun\b",
            r"\bexecute\b",
            r"\bterminal\b",
            r"\bcommand\b",
        ),
        "web_search": (
            r"\bweb\b",
            r"\binternet\b",
            r"\bgoogle\b",
            r"\bsearch online\b",
            r"\blatest\b",
            r"\bnews\b",
        ),
    }

    def route(self, prompt: str) -> IntentResult:
        """Route a request to the correct execution pipeline."""

        text = prompt.lower()

        for tool, patterns in self._DETERMINISTIC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return IntentResult(
                        pipeline=PipelineType.DETERMINISTIC,
                        confidence=1.0,
                        tool=tool,
                    )

        if self._requires_reasoning(text):
            return IntentResult(
                pipeline=PipelineType.REASONING,
                confidence=0.9,
            )

        if self._requires_semantic(text):
            return IntentResult(
                pipeline=PipelineType.SEMANTIC,
                confidence=0.8,
            )

        return IntentResult(
            pipeline=PipelineType.AMBIGUOUS,
            confidence=0.0,
        )

    @staticmethod
    def _requires_reasoning(text: str) -> bool:
        """Return whether reasoning is required."""

        reasoning_keywords = (
            "plan",
            "analyze",
            "design",
            "architect",
            "debug",
            "compare",
            "refactor",
            "solve",
        )

        return any(keyword in text for keyword in reasoning_keywords)

    @staticmethod
    def _requires_semantic(text: str) -> bool:
        """Return whether semantic understanding is required."""

        semantic_keywords = (
            "summarize",
            "explain",
            "describe",
            "what",
            "why",
            "how",
        )

        return any(keyword in text for keyword in semantic_keywords)