from __future__ import annotations

from pathlib import Path

from adityacli.workspace import WorkspaceManager
from .parser_models import RuntimePlan
from .constants import CHARACTERS_PER_TOKEN
from .context_models import (
    ContextBundle,
    ContextDocument,
    ContextSource,
)

class ContextBuilder:
    """Build deterministic context for language models."""

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self._workspace = workspace_manager

    def build(
        self,
        plan: RuntimePlan,
        context_budget: int,
    ) -> ContextBundle:

        bundle = ContextBundle()

        for step in plan.steps:

            match step.tool:

                case "read_file":
                    path = Path(str(step.arguments["path"]))

                    bundle.documents.extend(
                        self._build_file(
                            path,
                            context_budget,
                        ).documents
                    )

                case _:
                    continue

        return bundle
    

    def _build_file(
        self,
        path: Path,
        context_budget: int,
    ) -> ContextBundle:
        """Build context from a workspace file."""

        file_path = self._workspace.resolve_existing_file(path)
        
        character_budget = (
            context_budget
            * CHARACTERS_PER_TOKEN
        )

        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )[:character_budget]

        return ContextBundle(
            documents=[
                ContextDocument(
                    source=ContextSource.FILESYSTEM,
                    title=file_path.name,
                    path=file_path.relative_to(
                        self._workspace.workspace.root
                    ),
                    content=content,
                )
            ]
        )

    def _build_workspace(
        self,
        context_budget: int,
    ) -> ContextBundle:
        raise NotImplementedError()

    def _build_project(
        self,
        context_budget: int,
    ) -> ContextBundle:
        raise NotImplementedError()

    def _build_search(
        self,
        text: str,
        context_budget: int,
    ) -> ContextBundle:
        """Reduce arbitrary text."""

        character_budget = (
            context_budget
            * CHARACTERS_PER_TOKEN
        )

        return ContextBundle(
            documents=[
                ContextDocument(
                    source=ContextSource.SEARCH,
                    title="Search Result",
                    content=text[:character_budget],
                )
            ]
        )
