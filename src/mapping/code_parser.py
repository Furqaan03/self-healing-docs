"""Parse Python source into semantic chunks (functions/classes) with stable IDs."""
from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class CodeChunk:
    identifier: str        # e.g. "module.py::function_name"
    kind: str              # "function" | "class"
    name: str
    signature: str
    docstring: str
    source_file: str


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = [a.arg for a in node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return f"{node.name}({', '.join(args)})"


def parse_python(source: str, source_file: str) -> list[CodeChunk]:
    """Extracts top-level and class-level functions and class definitions."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    chunks: list[CodeChunk] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(CodeChunk(
                identifier=f"{source_file}::{node.name}",
                kind="function", name=node.name,
                signature=_format_signature(node),
                docstring=ast.get_docstring(node) or "",
                source_file=source_file,
            ))
        elif isinstance(node, ast.ClassDef):
            chunks.append(CodeChunk(
                identifier=f"{source_file}::{node.name}",
                kind="class", name=node.name,
                signature=f"class {node.name}",
                docstring=ast.get_docstring(node) or "",
                source_file=source_file,
            ))
    return chunks
