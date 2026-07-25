from __future__ import annotations

from pathlib import Path

from .builder import RepositoryBuilder
from .models import (
    ClassSymbol,
    FileSymbol,
    FunctionSymbol,
    MethodSymbol,
    RepositoryIndex,
    RepositoryReference,
)
from .symbol_extractor import SymbolExtractor

class RepositoryManager:
    """Manage the repository index."""

    def __init__(self) -> None:
        self._index = RepositoryIndex()
        self._builder = RepositoryBuilder()
        self._symbol_extractor = SymbolExtractor()

    @property
    def index(self) -> RepositoryIndex:
        """Return the current repository index."""

        return self._index

    def build(
        self,
        workspace: Path,
    ) -> None:
        """Build the repository index."""

        self._index = self._builder.build(
            workspace,
        )

    def rebuild(
        self,
        workspace: Path,
    ) -> None:
        """Rebuild the repository index."""

        self.build(workspace)

    def files(
        self,
    ) -> list[FileSymbol]:
        """Return all indexed files."""

        return self._index.files

    def classes(
        self,
    ) -> list[ClassSymbol]:
        """Return all indexed classes."""

        return [
            cls
            for file in self._index.files
            for cls in file.classes
        ]

    def functions(
        self,
    ) -> list[FunctionSymbol]:
        """Return all indexed functions."""

        return [
            function
            for file in self._index.files
            for function in file.functions
        ]

    def find_file(
        self,
        path: Path,
    ) -> FileSymbol | None:
        """Find a file by relative path."""

        for file in self._index.files:
            if file.path == path:
                return file

        return None

    def find_class(
        self,
        name: str,
    ) -> ClassSymbol | None:
        """Find a class by name."""

        for cls in self.classes():
            if cls.name == name:
                return cls

        return None

    def find_function(
        self,
        name: str,
    ) -> FunctionSymbol | None:
        """Find a function by name."""

        for function in self.functions():
            if function.name == name:
                return function

        return None

    def find_method(
        self,
        class_name: str,
        method_name: str,
    ) -> MethodSymbol | None:
        """Find a method by class and method name."""

        cls = self.find_class(class_name)

        if cls is None:
            return None

        for method in cls.methods:
            if method.name == method_name:
                return method

        return None


    def file_for_symbol(
        self,
        symbol: str,
    ) -> FileSymbol | None:
        """Return the file containing a repository symbol."""

        class_name: str | None = None
        method_name: str | None = None

        if "." in symbol:
            class_name, _, method_name = symbol.partition(".")

        for file in self._index.files:

            if class_name is not None:

                for cls in file.classes:

                    if cls.name != class_name:
                        continue

                    if any(
                        method.name == method_name
                        for method in cls.methods
                    ):
                        return file

                continue

            if any(
                cls.name == symbol
                for cls in file.classes
            ):
                return file

            if any(
                function.name == symbol
                for function in file.functions
            ):
                return file

        return None

    
    def exists_class(
        self,
        name: str,
    ) -> bool:

        return self.find_class(name) is not None

    def exists_function(
        self,
        name: str,
    ) -> bool:

        return self.find_function(name) is not None

    def exists_file(
        self,
        path: Path,
    ) -> bool:

        return self.find_file(path) is not None

    def find_callers(
        self,
        name: str,
    ) -> list[FunctionSymbol | MethodSymbol]:
        """Return every function or method that calls a symbol."""

        callers: list[
            FunctionSymbol | MethodSymbol
        ] = []

        for function in self.functions():

            if any(
                call.name == name
                for call in function.calls
            ):
                callers.append(function)

        for cls in self.classes():

            for method in cls.methods:

                if any(
                    call.name == name
                    for call in method.calls
                ):
                    callers.append(method)

        return callers

    def read_lines(
        self,
        path: Path,
        start: int,
        end: int,
    ) -> str:
        """Read an inclusive line range from a source file."""

        lines = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()

        return "\n".join(
            lines[start - 1 : end]
        )

    def resolve_class(
        self,
        name: str,
    ) -> RepositoryReference | None:

        cls = self.find_class(name)

        if cls is None:
            return None

        file = self.file_for_symbol(name)

        if file is None:
            return None

        return RepositoryReference(
            path=file.path,
            title=cls.name,
            start_line=cls.line,
            end_line=cls.end_line or cls.line,
        )


    def resolve_function(
        self,
        name: str,
    ) -> RepositoryReference | None:

        function = self.find_function(name)

        if function is None:
            return None

        file = self.file_for_symbol(name)

        if file is None:
            return None

        return RepositoryReference(
            path=file.path,
            title=function.name,
            start_line=function.line,
            end_line=function.end_line or function.line,
        )


    def resolve_method(
        self,
        class_name: str,
        method_name: str,
    ) -> RepositoryReference | None:

        method = self.find_method(
            class_name,
            method_name,
        )

        if method is None:
            return None

        file = self.file_for_symbol(
            f"{class_name}.{method_name}",
        )

        if file is None:
            return None

        return RepositoryReference(
            path=file.path,
            title=f"{class_name}.{method_name}",
            start_line=method.line,
            end_line=method.end_line or method.line,
        )

    def resolve_callers(
        self,
        name: str,
    ) -> list[RepositoryReference]:

        references: list[RepositoryReference] = []

        for function in self.functions():

            if any(
                call.name == name
                for call in function.calls
            ):

                file = self.file_for_symbol(
                    function.name,
                )

                if file is None:
                    continue

                references.append(
                    RepositoryReference(
                        path=file.path,
                        title=function.name,
                        start_line=function.line,
                        end_line=function.end_line or function.line,
                    )
                )

        for file in self._index.files:

            for cls in file.classes:

                for method in cls.methods:

                    if not any(
                        call.name == name
                        for call in method.calls
                    ):
                        continue

                    references.append(
                        RepositoryReference(
                            path=file.path,
                            title=f"{cls.name}.{method.name}",
                            start_line=method.line,
                            end_line=method.end_line or method.line,
                        )
                    )

        return references

    def resolve_symbol(
        self,
        symbol: str,
    ) -> RepositoryReference | None:
        """Resolve any repository symbol."""

        if "." in symbol:

            class_name, _, method_name = symbol.partition(".")

            return self.resolve_method(
                class_name,
                method_name,
            )

        reference = self.resolve_class(symbol)

        if reference is not None:
            return reference

        reference = self.resolve_function(symbol)

        if reference is not None:
            return reference

        for cls in self.classes():

            reference = self.resolve_method(
                cls.name,
                symbol,
            )

            if reference is not None:
                return reference

        return None