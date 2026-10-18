from pathlib import Path

from adityacli.config import AppConfig
from adityacli.core.workspace_guard import WorkspaceGuard


class PathResolver:
    """Shared, pruned filename lookup with bounded optional results."""

    def __init__(self, config: AppConfig) -> None:
        self._guard = WorkspaceGuard(config)

    @property
    def workspace(self) -> Path:
        return self._guard.workspace

    def find_by_name(self, query: str, limit: int | None = None) -> list[Path]:
        # Validate before walking: traversal must not become a name search.
        self._guard.resolve(query)
        query_lower = query.lower()
        matches = []
        for path in self._guard.iter_files(max_size=True):
            if query_lower in (path.stem.lower(), path.name.lower()):
                matches.append(path)
                if limit is not None and len(matches) >= limit:
                    break
        return matches
