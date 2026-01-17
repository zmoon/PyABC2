from pathlib import Path
from tempfile import tempdir

from pyabc2.html import html, open_html


def test_html_basic():
    abc = "ABCD"
    html_str = html(abc)
    assert abc in html_str


def test_open_html(monkeypatch):
    called = {}

    def mock_open_new_tab(url: str) -> None:
        called["url"] = url

    def mock_input(arg: str) -> str:
        return "\n"

    monkeypatch.setattr("webbrowser.open_new_tab", mock_open_new_tab)
    monkeypatch.setattr("builtins.input", mock_input)

    abc = "ABCD"
    open_html(abc)

    url = called["url"]
    assert url.startswith(tempdir)
    assert Path(url).exists(), "haven't exited yet"
