from __future__ import annotations

import ntpath
import os
import stat
from adityacli.core.operations import check_operation
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO

from adityacli.config import AppConfig
from adityacli.exceptions import FileTooLargeError, InvalidPathError


IGNORE_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".sessions", "build", "dist",
})
IGNORE_SUFFIXES = frozenset({".pyc", ".pyo"})


class WorkspaceGuard:
    """Confine project data to the resolved launch directory."""

    def __init__(self, config: AppConfig | Path) -> None:
        self._workspace = (config if isinstance(config, Path) else config.workspace.root).resolve()
        self._max_file_size = 2 * 1024 * 1024 if isinstance(config, Path) else config.workspace.max_file_size

    @property
    def workspace(self) -> Path:
        return self._workspace

    @staticmethod
    def _linked(info: os.stat_result) -> bool:
        return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)

    def resolve(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        drive, _ = ntpath.splitdrive(relative_path)
        if not relative_path or candidate.is_absolute() or candidate.anchor or drive or ":" in relative_path or ".." in candidate.parts:
            raise InvalidPathError(f"Expected a workspace-relative path: {relative_path}")
        path = self._workspace / candidate
        resolved = path.resolve()
        if not resolved.is_relative_to(self._workspace):
            raise InvalidPathError(f"Path is outside the workspace: {relative_path}")
        # Reject reparse points even when they happen to resolve inside the
        # workspace, so a redirected directory cannot be traversed later.
        current = self._workspace
        for part in candidate.parts:
            current = current / part
            try:
                info = current.lstat()
            except FileNotFoundError:
                continue
            if self._linked(info) or (stat.S_ISREG(info.st_mode) and info.st_nlink > 1):
                raise InvalidPathError(f"Linked paths are not allowed: {relative_path}")
        return resolved

    def existing_file(self, relative_path: str) -> Path:
        path = self.resolve(relative_path)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise InvalidPathError(f"{relative_path} is not a file.")
        if info.st_size > self._max_file_size:
            raise FileTooLargeError(f"{relative_path} exceeds the maximum file size.")
        return path

    def relative_path(self, relative_path: str) -> str:
        """One cache identity for case and separator aliases on this platform."""
        path = self.resolve(relative_path).relative_to(self._workspace)
        return Path(os.path.normcase(str(path))).as_posix()

    def new_file(self, relative_path: str) -> Path:
        path = self.resolve(relative_path)
        if path.exists() and not path.is_file():
            raise InvalidPathError(f"{relative_path} is not a file.")
        return path

    @contextmanager
    def open_text(self, relative_path: str, encoding: str = "utf-8") -> Iterator[TextIO]:
        path = self.existing_file(relative_path)
        with path.open("rb") as raw:
            info = os.fstat(raw.fileno())
            if info.st_size > self._max_file_size:
                raise FileTooLargeError(f"{relative_path} exceeds the maximum file size.")
            if info.st_nlink > 1 or self.resolve(relative_path).stat().st_ino != info.st_ino:
                raise InvalidPathError(f"File changed or is linked: {relative_path}")
            if b"\x00" in raw.read(4096):
                raise InvalidPathError(f"Binary files are not supported: {relative_path}")
            raw.seek(0)
            from io import TextIOWrapper
            with TextIOWrapper(raw, encoding=encoding, newline="") as text:
                yield text

    def read_text(self, relative_path: str, encoding: str = "utf-8") -> str:
        with self.open_text(relative_path, encoding) as file:
            content = file.read(self._max_file_size + 1)
        if len(content.encode(encoding)) > self._max_file_size:
            raise FileTooLargeError(f"{relative_path} exceeds the maximum file size.")
        if "\x00" in content:
            raise InvalidPathError(f"Binary files are not supported: {relative_path}")
        return content

    def iter_files(self, *, max_size: bool = False) -> Iterator[Path]:
        """Prune excluded directories before descent; never follow links."""
        pending = [self._workspace]
        while pending:
            check_operation()
            directory = pending.pop()
            self.resolve(str(directory.relative_to(self._workspace)) or ".")
            try:
                with os.scandir(directory) as entries:
                    for entry in sorted(entries, key=lambda entry: entry.name.casefold()):
                        check_operation()
                        if entry.name in IGNORE_DIRS:
                            continue
                        try:
                            info = entry.stat(follow_symlinks=False)
                        except OSError:
                            continue
                        if self._linked(info):
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            pending.append(Path(entry.path))
                        elif stat.S_ISREG(info.st_mode) and info.st_nlink <= 1:
                            path = Path(entry.path)
                            # Windows DirEntry.stat reports st_nlink=0;
                            # query the file for its actual hard-link count.
                            if os.name == "nt" and path.stat().st_nlink > 1:
                                continue
                            if path.suffix.lower() not in IGNORE_SUFFIXES and (not max_size or info.st_size <= self._max_file_size):
                                yield path
            except (OSError, InvalidPathError):
                continue
