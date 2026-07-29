from pathlib import Path

import pytest

from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.file_manager import FileManager
from adityacli.exceptions import (
    FileAlreadyExistsError,
    InvalidPathError,
)


@pytest.fixture
def manager(tmp_path: Path) -> FileManager:
    config = AppConfig(
        workspace=WorkspaceConfig(root=tmp_path),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )
    return FileManager(config)


def test_write_creates_file(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    manager.write("hello.txt", "hello")

    assert (tmp_path / "hello.txt").read_text() == "hello"


def test_write_creates_parent_directories(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    manager.write(
        "src/core/test.txt",
        "abc",
    )

    assert (
        tmp_path / "src/core/test.txt"
    ).read_text() == "abc"


def test_write_existing_file_without_overwrite(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    path = tmp_path / "a.txt"
    path.write_text("old")

    with pytest.raises(FileAlreadyExistsError):
        manager.write(
            "a.txt",
            "new",
        )


def test_write_existing_file_with_overwrite(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    path = tmp_path / "a.txt"
    path.write_text("old")

    manager.write(
        "a.txt",
        "new",
        overwrite=True,
    )

    assert path.read_text() == "new"


def test_write_many(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    manager.write_many(
        {
            "a.txt": "one",
            "dir/b.txt": "two",
        }
    )

    assert (tmp_path / "a.txt").read_text() == "one"
    assert (tmp_path / "dir/b.txt").read_text() == "two"


def test_write_many_existing_file_without_overwrite(
    manager: FileManager,
    tmp_path: Path,
) -> None:
    (tmp_path / "a.txt").write_text("old")

    with pytest.raises(FileAlreadyExistsError):
        manager.write_many(
            {
                "a.txt": "new",
                "b.txt": "two",
            }
        )


def test_workspace_escape_is_rejected(
    manager: FileManager,
) -> None:
    with pytest.raises(InvalidPathError):
        manager.write(
            "../secret.txt",
            "secret",
        )


def test_absolute_path_is_rejected(
    manager: FileManager,
) -> None:
    path = Path.cwd().anchor + "temp.txt"

    with pytest.raises(InvalidPathError):
        manager.write(
            path,
            "content",
        )


def test_write_many_workspace_escape(
    manager: FileManager,
) -> None:
    with pytest.raises(InvalidPathError):
        manager.write_many(
            {
                "../evil.txt": "bad",
            }
        )