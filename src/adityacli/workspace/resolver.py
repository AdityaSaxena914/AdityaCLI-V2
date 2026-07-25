from __future__ import annotations

from pathlib import Path

from .index import WorkspaceIndex


class WorkspaceFileResolver:
    """Resolve workspace file references deterministically."""

    def __init__(
        self,
        index: WorkspaceIndex,
    ) -> None:
        self._index = index

    def resolve(
        self,
        prompt: str,
        path: Path,
    ) -> Path | None:
        """
        Resolve a filename into a workspace-relative path.
        """

        if len(path.parts) > 1:
            return path

        matches = self._index.lookup(path.name)

        if not matches:
            return None

        prompt = prompt.lower()

        ranked = sorted(
            matches,
            key=lambda candidate: (
                -self._score(prompt, candidate),
                len(candidate.parts),
                len(candidate.as_posix()),
                candidate.as_posix(),
            ),
        )

        return ranked[0]

    def _score(
        self,
        prompt: str,
        path: Path,
    ) -> int:
        """
        Higher score == better match.
        """

        score = 0

        # Prefer src/
        if path.parts and path.parts[0] == "src":
            score += 100

        # Prefer directory names mentioned in prompt
        for part in path.parts[:-1]:
            if part.lower() in prompt:
                score += 50

        # Prefer package names
        for part in path.parts:
            if part.lower() in prompt:
                score += 20

        # Penalize tests/examples/docs
        if any(
            part.lower() in {
                "tests",
                "test",
                "examples",
                "docs",
            }
            for part in path.parts
        ):
            score -= 25

        return score

    def candidates(
        self,
        filename: str,
    ) ->list[Path]:

        return self._index.lookup(filename)