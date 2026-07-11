"""Link doc sections to code chunks. Heuristic (symbol-name match) first;
embeddings enhance it (optional, injected)."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.mapping.code_parser import CodeChunk
from src.mapping.doc_parser import DocSection


@dataclass
class LinkGraph:
    # code chunk identifier -> set of doc heading_paths that reference it
    code_to_docs: dict[str, set[str]] = field(default_factory=dict)

    def add_link(self, code_id: str, doc_path: str) -> None:
        self.code_to_docs.setdefault(code_id, set()).add(doc_path)

    def docs_for_code(self, code_id: str) -> set[str]:
        return self.code_to_docs.get(code_id, set())

    def to_dict(self) -> dict[str, list[str]]:
        return {k: sorted(v) for k, v in self.code_to_docs.items()}


def build_link_graph(code_chunks: list[CodeChunk], doc_sections: list[DocSection]) -> LinkGraph:
    """Heuristic linking: if a doc section mentions a code chunk's name, link them."""
    graph = LinkGraph()
    name_to_chunks: dict[str, list[CodeChunk]] = {}
    for chunk in code_chunks:
        name_to_chunks.setdefault(chunk.name, []).append(chunk)

    for section in doc_sections:
        for ref in section.code_references:
            for chunk in name_to_chunks.get(ref, []):
                graph.add_link(chunk.identifier, section.heading_path)
    return graph
