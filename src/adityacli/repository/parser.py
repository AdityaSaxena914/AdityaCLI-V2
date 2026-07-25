from __future__ import annotations

import ast
from pathlib import Path

from .models import (
    ClassSymbol,
    FileSymbol,
    FunctionSymbol,
    ImportSymbol,
    MethodSymbol,
    CallSite,
)


class RepositoryParser:
    """Parse Python source files into repository symbols."""

    def parse(
        self,
        path: Path,
    ) -> FileSymbol:

        source = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )

        file = FileSymbol(
            path=path,
        )

        for node in tree.body:

            if isinstance(node, ast.Import):
                file.imports.extend(
                    self._parse_import(node)
                )

            elif isinstance(node, ast.ImportFrom):
                file.imports.extend(
                    self._parse_import_from(node)
                )

            elif isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                file.functions.append(
                    self._parse_function(node)
                )

            elif isinstance(node, ast.ClassDef):
                file.classes.append(
                    self._parse_class(node)
                )

        return file

    def _parse_import(
        self,
        node: ast.Import,
    ) -> list[ImportSymbol]:

        return [
            ImportSymbol(
                module=None,
                name=alias.name,
                alias=alias.asname,
            )
            for alias in node.names
        ]

    def _parse_import_from(
        self,
        node: ast.ImportFrom,
    ) -> list[ImportSymbol]:

        return [
            ImportSymbol(
                module=node.module,
                name=alias.name,
                alias=alias.asname,
            )
            for alias in node.names
        ]

    def _parse_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionSymbol:

        return FunctionSymbol(
            name=node.name,
            line=node.lineno,
            end_line=getattr(
                node,
                "end_lineno",
                None,
            ),
            docstring=ast.get_docstring(node),
            calls=self._parse_calls(node),
        )
    

    def _parse_class(
        self,
        node: ast.ClassDef,
    ) -> ClassSymbol:

        methods: list[MethodSymbol] = []

        for child in node.body:
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                methods.append(
                    MethodSymbol(
                        name=child.name,
                        line=child.lineno,
                        end_line=getattr(
                            child,
                            "end_lineno",
                            None,
                        ),
                        docstring=ast.get_docstring(child),
                        calls=self._parse_calls(child),
                    )
                )

        return ClassSymbol(
            name=node.name,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", None),
            docstring=ast.get_docstring(node),
            methods=methods,
        )

    def _parse_calls(
        self,
        node: ast.AST,
    ) -> list[CallSite]:
        """Extract function and method calls."""

        calls: list[CallSite] = []

        for child in ast.walk(node):

            if not isinstance(child, ast.Call):
                continue

            name: str | None = None

            if isinstance(child.func, ast.Name):
                name = child.func.id

            elif isinstance(child.func, ast.Attribute):
                name = child.func.attr

            if name is None:
                continue

            calls.append(
                CallSite(
                    name=name,
                    line=child.lineno,
                )
            )

        return calls