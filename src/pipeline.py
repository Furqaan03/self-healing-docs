"""Orchestrates: parse code+docs -> build link graph -> diff -> find affected docs.

The staleness verification and repair steps (LLM-backed) are invoked per suspect
section; this module wires the offline mapping/detection stages together."""
from __future__ import annotations

from dataclasses import dataclass

from src.detection.diff_parser import filter_meaningful, parse_diff
from src.mapping.code_parser import parse_python
from src.mapping.doc_parser import parse_markdown
from src.mapping.link_graph import build_link_graph


@dataclass
class SuspectSection:
    doc_path: str
    triggered_by_file: str


def find_suspect_sections(
    code_files: dict[str, str],
    doc_files: dict[str, str],
    diff_text: str,
) -> list[SuspectSection]:
    """Returns doc sections that MIGHT be stale given the diff — the candidates
    that then go to LLM staleness verification."""
    code_chunks = []
    for path, source in code_files.items():
        code_chunks.extend(parse_python(source, path))

    doc_sections = []
    for source in doc_files.values():
        doc_sections.extend(parse_markdown(source))

    graph = build_link_graph(code_chunks, doc_sections)

    changed_files = {c.path for c in filter_meaningful(parse_diff(diff_text))}

    suspects: list[SuspectSection] = []
    seen: set[tuple[str, str]] = set()
    for chunk in code_chunks:
        if chunk.source_file not in changed_files:
            continue
        for doc_path in graph.docs_for_code(chunk.identifier):
            key = (doc_path, chunk.source_file)
            if key not in seen:
                seen.add(key)
                suspects.append(SuspectSection(doc_path=doc_path, triggered_by_file=chunk.source_file))
    return suspects
