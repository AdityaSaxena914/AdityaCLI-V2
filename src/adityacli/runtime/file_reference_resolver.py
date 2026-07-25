from __future__ import annotations

import re
from pathlib import Path

from adityacli.workspace import WorkspaceManager


class FileReferenceResolver:
    """Rewrite file references inside prompts."""

    _PATTERN = re.compile(
        r"((?:[\w.-]+[/\\])*[\w.-]+\.[A-Za-z0-9]+)"
    )

    def __init__(
        self,
        workspace: WorkspaceManager,
    ) -> None:
        self._workspace = workspace

    def resolve(
        self,
        prompt: str,
    ) -> str:

        def replace(
            match: re.Match[str],
        ) -> str:

            token = match.group(1)

            path = Path(token)

            #
            # Already contains directories
            #
            if len(path.parts) > 1:
                return token

            candidates = self._workspace.file_candidates(
                path.name
            )

            if not candidates:
                return token

            
            scores = {
                candidate: self._score(
                    prompt,
                    candidate,
                )
                for candidate in candidates
            }

            highest = max(scores.values())

            best = [
                candidate
                for candidate, score in scores.items()
                if score == highest
            ]


            if len(best) == 1:
                return best[0].as_posix()

    
            from .exceptions import AmbiguousFileReferenceError

            raise AmbiguousFileReferenceError(
                filename=path.name,
                matches=[
                    p.as_posix()
                    for p in best
                ],
            )

        return self._PATTERN.sub(
            replace,
            prompt,
        )

    def _score(
        self,
        prompt: str,
        path: Path,
    ) -> int:

        prompt = prompt.lower()

        score = 0

        #
        # Directory names
        #
        for part in path.parts[:-1]:

            if part.lower() in prompt:
                score += 100

        #
        # Prefer src
        #
        if path.parts and path.parts[0] == "src":
            score += 25

        #
        # Penalize tests/examples
        #
        if any(
            x in {
                "tests",
                "test",
                "examples",
                "docs",
            }
            for x in path.parts
        ):
            score -= 20

        #
        # Prefer shorter paths
        #
        score -= len(path.parts)

        return score

    