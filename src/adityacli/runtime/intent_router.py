from __future__ import annotations

from .grammars import filesystem
from .models import (
    IntentResult,
    IntentType,
    PipelineType,
)


class IntentRouter:
    """Deterministically classify user requests."""

    _SEARCH = (
        "find",
        "search",
        "locate",
    )

    _TERMINAL = (
        "run",
        "execute",
    )

    _GIT = (
        "git",
        "commit",
        "branch",
        "checkout",
        "merge",
        "pull",
        "push",
        "status",
        "diff",
        "log",
    )

    _SEMANTIC = (
        "explain",
        "summarize",
        "describe",
        "what",
        "why",
        "how",
    )

    _REASONING = (
        "analyze",
        "analyse",
        "plan",
        "design",
        "architect",
        "implement",
        "build",
        "refactor",
        "optimize",
        "debug",
        "solve",
    )

    def route(
        self,
        prompt: str,
    ) -> IntentResult:
        """Classify a request without using an LLM."""

        text = prompt.lower().strip()

        if not text:
            return IntentResult(
                intent=IntentType.AMBIGUOUS,
                confidence=0.0,
            )

        verb = text.split(maxsplit=1)[0]



        if verb in filesystem.READ:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="read_file",
                confidence=1.0,
            )

        if verb in filesystem.WRITE:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="write_file",
                confidence=1.0,
            )

        if verb in filesystem.EDIT:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="edit_file",
                confidence=1.0,
            )

        if verb in filesystem.COPY:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="copy_file",
                confidence=1.0,
            )

        if verb in filesystem.MOVE:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="move_file",
                confidence=1.0,
            )

        if verb in filesystem.DELETE:
            return IntentResult(
                intent=IntentType.FILESYSTEM,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="delete_file",
                confidence=1.0,
            )



        if verb in self._SEARCH:
            return IntentResult(
                intent=IntentType.SEARCH,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="workspace_search",
                confidence=1.0,
            )



        if verb in self._TERMINAL:
            return IntentResult(
                intent=IntentType.TERMINAL,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="terminal",
                confidence=1.0,
            )



        if verb in self._GIT:
            return IntentResult(
                intent=IntentType.GIT,
                pipeline=PipelineType.DETERMINISTIC,
                tool_name="git_status",
                confidence=1.0,
            )



        if any(keyword in text for keyword in self._REASONING):
            return IntentResult(
                intent=IntentType.REASONING,
                pipeline=PipelineType.REASONING,
                confidence=0.95,
            )



        if any(keyword in text for keyword in self._SEMANTIC):
            return IntentResult(
                intent=IntentType.SEMANTIC,
                pipeline=PipelineType.SEMANTIC,
                confidence=0.90,
            )

        return IntentResult(
            intent=IntentType.AMBIGUOUS,
            confidence=0.0,
        )