from src.mapping.code_parser import parse_python

SRC = '''
def connect_db(url, timeout=30):
    """Connect to the database."""
    return url

class Server:
    """The API server."""
    def start(self, port):
        return port
'''


def test_extracts_functions_and_classes():
    chunks = parse_python(SRC, "app.py")
    names = {c.name for c in chunks}
    assert "connect_db" in names
    assert "Server" in names
    assert "start" in names


def test_signature_includes_args():
    chunks = parse_python(SRC, "app.py")
    connect = next(c for c in chunks if c.name == "connect_db")
    assert connect.signature == "connect_db(url, timeout)"


def test_stable_identifier():
    chunks = parse_python(SRC, "app.py")
    connect = next(c for c in chunks if c.name == "connect_db")
    assert connect.identifier == "app.py::connect_db"


def test_syntax_error_returns_empty():
    assert parse_python("def broken(", "bad.py") == []
