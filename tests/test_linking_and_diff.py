from src.detection.diff_parser import filter_meaningful, has_meaningful_change, parse_diff
from src.mapping.code_parser import parse_python
from src.mapping.doc_parser import parse_markdown
from src.mapping.link_graph import build_link_graph
from src.pipeline import find_suspect_sections

CODE = 'def connect_db(url, timeout=30):\n    """Connect."""\n    return url\n'
DOC = "# Database\n\nCall connect_db to connect with a default timeout of 30.\n"


def test_link_graph_connects_doc_to_code():
    chunks = parse_python(CODE, "db.py")
    sections = parse_markdown(DOC)
    graph = build_link_graph(chunks, sections)
    assert "db.py::connect_db" in graph.code_to_docs
    assert "Database" in graph.docs_for_code("db.py::connect_db")


def test_diff_parse_added_removed():
    diff = "+++ b/db.py\n+def connect_db(url, timeout=60):\n-def connect_db(url, timeout=30):\n"
    changes = parse_diff(diff)
    assert changes[0].path == "db.py"
    assert any("timeout=60" in l for l in changes[0].added_lines)


def test_meaningful_change_filter():
    diff = "+++ b/db.py\n+def connect_db(url, timeout=60):\n"
    changes = parse_diff(diff)
    assert has_meaningful_change(changes[0]) is True


def test_comment_only_change_not_meaningful():
    diff = "+++ b/db.py\n+# just a comment update\n"
    changes = parse_diff(diff)
    assert has_meaningful_change(changes[0]) is False


def test_pipeline_finds_suspects():
    diff = "+++ b/db.py\n+def connect_db(url, timeout=60):\n-def connect_db(url, timeout=30):\n"
    suspects = find_suspect_sections({"db.py": CODE}, {"README.md": DOC}, diff)
    assert any(s.doc_path == "Database" for s in suspects)
