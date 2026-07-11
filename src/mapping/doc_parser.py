"""Parse markdown docs into sections, each tagged with the code symbols it mentions."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DocSection:
    heading_path: str            # e.g. "Configuration > Environment Variables"
    content: str
    code_references: list[str] = field(default_factory=list)


# Identifiers that look like code: snake_case, CamelCase, or `backticked` tokens.
_CODE_TOKEN = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`|\b([a-z_][a-z0-9_]+_[a-z0-9_]+)\b|\b([A-Z][a-zA-Z0-9]+[A-Z][a-zA-Z0-9]*)\b")


def _extract_code_refs(text: str) -> list[str]:
    refs = set()
    for m in _CODE_TOKEN.finditer(text):
        token = m.group(1) or m.group(2) or m.group(3)
        if token:
            refs.add(token)
    return sorted(refs)


def parse_markdown(source: str) -> list[DocSection]:
    sections: list[DocSection] = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_path = ""

    def flush():
        nonlocal current_lines
        if current_path or current_lines:
            content = "\n".join(current_lines).strip()
            sections.append(DocSection(heading_path=current_path, content=content, code_references=_extract_code_refs(content)))
        current_lines = []

    for line in source.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            heading_stack = [(lvl, t) for lvl, t in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_path = " > ".join(t for _, t in heading_stack)
        else:
            current_lines.append(line)
    flush()
    return [s for s in sections if s.content or s.heading_path]
