from src.mapping.doc_parser import parse_markdown

DOC = """# Configuration

Set the `DATABASE_URL` variable.

## Environment Variables

Call connect_db to open a connection. The `Server` class handles requests.
"""


def test_heading_paths_nested():
    sections = parse_markdown(DOC)
    paths = {s.heading_path for s in sections}
    assert "Configuration" in paths
    assert "Configuration > Environment Variables" in paths


def test_code_references_extracted():
    sections = parse_markdown(DOC)
    env_section = next(s for s in sections if "Environment" in s.heading_path)
    assert "connect_db" in env_section.code_references
    assert "Server" in env_section.code_references


def test_backticked_reference():
    sections = parse_markdown(DOC)
    config = next(s for s in sections if s.heading_path == "Configuration")
    assert "DATABASE_URL" in config.code_references
