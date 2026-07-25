from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ImportSymbol(BaseModel):
    """Represents an import statement."""

    module: str | None = None
    name: str
    alias: str | None = None

class CallSite(BaseModel):
    """Represents a function or method call."""

    name: str

    line: int


class FunctionSymbol(BaseModel):
    """Represents a top-level function."""

    name: str

    line: int

    end_line: int | None = None

    docstring: str | None = None

    calls: list[CallSite] = Field(
        default_factory=list,
    )


class MethodSymbol(BaseModel):
    """Represents a class method."""

    name: str

    line: int

    end_line: int | None = None

    docstring: str | None = None

    calls: list[CallSite] = Field(
        default_factory=list,
    )


class ClassSymbol(BaseModel):
    """Represents a class."""

    name: str

    line: int

    end_line: int | None = None

    docstring: str | None = None

    methods: list[MethodSymbol] = Field(
        default_factory=list,
    )


class FileSymbol(BaseModel):
    """Represents a parsed source file."""

    path: Path

    imports: list[ImportSymbol] = Field(
        default_factory=list,
    )

    classes: list[ClassSymbol] = Field(
        default_factory=list,
    )

    functions: list[FunctionSymbol] = Field(
        default_factory=list,
    )


class RepositoryIndex(BaseModel):
    """Complete repository symbol index."""

    files: list[FileSymbol] = Field(
        default_factory=list,
    )


class RepositoryReference(BaseModel):
    """A resolved repository symbol."""

    path: Path

    title: str

    start_line: int

    end_line: int


