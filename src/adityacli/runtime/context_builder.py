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
from adityacli.repository.models import (
    RepositoryReference,
)
from adityacli.repository.query_type import RepositoryQueryType

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

        file_path = self._workspace.resolve_file(path)

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

    def _build_symbol(
        self,
        reference: RepositoryReference,
    ) -> ContextBundle:

        repository = self._workspace.repository

        content = repository.read_lines(
            reference.path,
            reference.start_line,
            reference.end_line,
        )

        return ContextBundle(
            documents=[
                ContextDocument(
                    source=ContextSource.FILESYSTEM,
                    title=reference.title,
                    path=reference.path,
                    content=content,
                )
            ]
        )

    def build_repository(
        self,
        query: RepositoryQueryType | None,
        target: str,
        references: list[RepositoryReference],
    ) -> ContextBundle:

        operation = query.name if query is not None else "UNKNOWN"

        bundle = ContextBundle(
            documents=[
                ContextDocument(
                    source=ContextSource.REPOSITORY,
                    title="Repository Query",
                    content=(
                        f"Operation: {operation}\n"
                        f"Target: {target}\n\n"
                        f"The following {len(references)} document(s) are the "
                        "complete deterministic results returned by the repository index.\n"
                        "Answer only from these documents.\n"
                        "Do not infer additional results."
                    ),
                )
            ]
        )

        for reference in references:
            bundle.documents.extend(
                self._build_symbol(reference).documents
            )

        return bundle