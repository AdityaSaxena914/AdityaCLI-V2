from __future__ import annotations

from pathlib import Path

from adityacli.workspace import WorkspaceManager

from .constants import CHARACTERS_PER_TOKEN


class ContextBuilder:
    """Build deterministic context for language models."""

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self._workspace = workspace_manager

    def build_file_context(
        self,
        path: Path,
        context_budget: int,
    ) -> str:
        """Build context from a workspace file."""

        file_path = self._workspace.resolve(path)

        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        character_budget = (
            context_budget
            * CHARACTERS_PER_TOKEN
        )

        return content[:character_budget]

    def build_workspace_context(
        self,
        context_budget: int,
    ) -> str:
        """Build workspace-level context."""

        raise NotImplementedError()

    def build_project_context(
        self,
        context_budget: int,
    ) -> str:
        """Build project context."""

        raise NotImplementedError()

    def build_search_context(
        self,
        text: str,
        context_budget: int,
    ) -> str:
        """Reduce arbitrary text."""

        character_budget = (
            context_budget
            * CHARACTERS_PER_TOKEN
        )

        return text[:character_budget]