"""Parse a unified git diff and filter for changes that could affect docs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class FileChange:
    path: str
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)


def parse_diff(diff_text: str) -> list[FileChange]:
    changes: list[FileChange] = []
    current: FileChange | None = None
    for line in diff_text.splitlines():
        m = re.match(r"^\+\+\+ b/(.*)$", line)
        if m:
            current = FileChange(path=m.group(1))
            changes.append(current)
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.removed_lines.append(line[1:])
    return changes


def _is_meaningful(line: str) -> bool:
    """Filters out comment-only and whitespace-only changes."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#") or stripped.startswith("//"):
        return False
    return True


# Signals that a change is behavioral / interface-affecting (worth checking docs for).
_SIGNIFICANT = re.compile(r"^\s*(def |class |async def |@app\.|[A-Z_]+\s*=|@router\.)")


def has_meaningful_change(change: FileChange) -> bool:
    """A change matters for docs if it adds/removes a signature, endpoint, config
    constant, or other behavioral line — not just comments or whitespace."""
    for line in change.added_lines + change.removed_lines:
        if _is_meaningful(line) and _SIGNIFICANT.search(line):
            return True
    return False


def filter_meaningful(changes: list[FileChange]) -> list[FileChange]:
    return [c for c in changes if c.path.endswith(".py") and has_meaningful_change(c)]
